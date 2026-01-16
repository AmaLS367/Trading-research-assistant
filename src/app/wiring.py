from pathlib import Path

from src.agents.news_analyst import NewsAnalyst
from src.agents.synthesizer import Synthesizer
from src.agents.technical_analyst import TechnicalAnalyst
from src.agents.verifier import VerifierAgent
from src.app.settings import settings
from src.core.pipeline_trace import PipelineTrace
from src.core.ports.clock import Clock
from src.core.ports.llm_provider import LlmProvider
from src.core.ports.llm_provider_name import (
    PROVIDER_DEEPSEEK_API,
    PROVIDER_OLLAMA_LOCAL,
    PROVIDER_OLLAMA_SERVER,
)
from src.core.ports.llm_tasks import (
    TASK_NEWS_ANALYSIS,
    TASK_SYNTHESIS,
    TASK_TECH_ANALYSIS,
    TASK_VERIFICATION,
)
from src.core.ports.market_data_provider import MarketDataProvider
from src.core.ports.news_provider import NewsProvider
from src.core.ports.orchestrator import OrchestratorProtocol
from src.core.ports.storage import Storage
from src.core.services.scheduler import Scheduler
from src.data_providers.forex.fallback_provider import FallbackMarketDataProvider
from src.data_providers.forex.oanda_provider import OandaProvider
from src.data_providers.forex.twelve_data_provider import TwelveDataProvider
from src.llm.deepseek.deepseek_client import DeepSeekClient
from src.llm.ollama.ollama_client import OllamaClient
from src.llm.providers.llm_router import LlmRouter
from src.news_providers.gdelt_provider import GDELTProvider
from src.news_providers.multi_news_provider import MultiNewsProvider
from src.news_providers.newsapi_provider import NewsAPIProvider
from src.runtime.loop.minute_loop import MinuteLoop
from src.runtime.orchestrator import RuntimeOrchestrator
from src.storage.artifacts.artifact_store import ArtifactStore
from src.storage.sqlite.connection import DBConnection
from src.storage.sqlite.repositories.candles_repository import CandlesRepository
from src.storage.sqlite.repositories.rationales_repository import RationalesRepository
from src.storage.sqlite.repositories.recommendations_repository import RecommendationsRepository
from src.storage.sqlite.repositories.runs_repository import RunsRepository
from src.storage.sqlite.repositories.verification_repository import VerificationRepository
from src.storage.sqlite.storage import SqliteStorage
from src.utils.time_utils import SystemClock


def create_market_data_provider() -> MarketDataProvider:
    oanda_provider: OandaProvider | None = None
    twelve_data_provider: TwelveDataProvider | None = None

    if settings.oanda_api_key:
        oanda_provider = OandaProvider(
            api_key=settings.oanda_api_key,
            base_url=settings.oanda_base_url,
        )

    if settings.twelve_data_api_key:
        twelve_data_provider = TwelveDataProvider(
            api_key=settings.twelve_data_api_key,
            base_url=settings.twelve_data_base_url,
        )

    if oanda_provider and twelve_data_provider:
        return FallbackMarketDataProvider(
            primary=oanda_provider,
            secondary=twelve_data_provider,
        )
    elif oanda_provider:
        return oanda_provider
    elif twelve_data_provider:
        return twelve_data_provider
    else:
        raise ValueError(
            "No market data provider configured. "
            "Set either OANDA_API_KEY or TWELVE_DATA_API_KEY in environment variables."
        )


def create_news_provider() -> NewsProvider:
    gdelt_provider = GDELTProvider(base_url=settings.gdelt_base_url)

    newsapi_provider: NewsAPIProvider | None = None
    if settings.newsapi_api_key:
        newsapi_provider = NewsAPIProvider(
            api_key=settings.newsapi_api_key,
            base_url=settings.newsapi_base_url,
        )

    if newsapi_provider:
        return MultiNewsProvider(primary=gdelt_provider, secondary=newsapi_provider)
    else:
        return MultiNewsProvider(primary=gdelt_provider, secondary=None)


def create_llm_providers() -> dict[str, LlmProvider]:
    providers: dict[str, LlmProvider] = {}

    ollama_local_url = settings._get_ollama_local_url()
    providers[PROVIDER_OLLAMA_LOCAL] = OllamaClient(
        base_url=ollama_local_url,
        model=settings.ollama_model or "llama3:latest",
        provider_name=PROVIDER_OLLAMA_LOCAL,
    )

    ollama_server_url = settings._get_ollama_server_url()
    if ollama_server_url:
        providers[PROVIDER_OLLAMA_SERVER] = OllamaClient(
            base_url=ollama_server_url,
            model=settings.ollama_model or "llama3:latest",
            provider_name=PROVIDER_OLLAMA_SERVER,
        )

    if settings.deepseek_api_key:
        deepseek_base = settings.deepseek_api_base or "https://api.deepseek.com"
        providers[PROVIDER_DEEPSEEK_API] = DeepSeekClient(
            base_url=deepseek_base,
            api_key=settings.deepseek_api_key,
            provider_name=PROVIDER_DEEPSEEK_API,
        )

    return providers


def create_llm_router() -> LlmRouter:
    providers = create_llm_providers()
    routing_config = settings.get_llm_routing_config()

    task_routings = {
        TASK_TECH_ANALYSIS: settings.get_tech_routing(),
        TASK_NEWS_ANALYSIS: settings.get_news_routing(),
        TASK_SYNTHESIS: settings.get_synthesis_routing(),
        TASK_VERIFICATION: settings.get_verifier_routing(),
    }

    return LlmRouter(providers, routing_config, task_routings)


def create_technical_analyst() -> TechnicalAnalyst:
    llm_router = create_llm_router()
    return TechnicalAnalyst(llm_router=llm_router)


def create_synthesizer() -> Synthesizer:
    llm_router = create_llm_router()
    return Synthesizer(llm_router=llm_router)


def create_news_analyst() -> NewsAnalyst:
    llm_router = create_llm_router()
    return NewsAnalyst(llm_router=llm_router)


def create_verifier_agent() -> VerifierAgent:
    llm_router = create_llm_router()
    return VerifierAgent(llm_router=llm_router)


def create_recommendations_repository() -> RecommendationsRepository:
    db = DBConnection(str(settings.storage_sqlite_db_path))
    return RecommendationsRepository(db)


def create_runs_repository() -> RunsRepository:
    db = DBConnection(str(settings.storage_sqlite_db_path))
    return RunsRepository(db)


def create_rationales_repository() -> RationalesRepository:
    db = DBConnection(str(settings.storage_sqlite_db_path))
    return RationalesRepository(db)


def create_verification_repository() -> VerificationRepository:
    db = DBConnection(str(settings.storage_sqlite_db_path))
    return VerificationRepository(db)


def create_candles_repository() -> CandlesRepository:
    db = DBConnection(str(settings.storage_sqlite_db_path))
    return CandlesRepository(db)


def create_storage() -> Storage:
    db = DBConnection(str(settings.storage_sqlite_db_path))
    return SqliteStorage(db)


def create_artifact_store() -> ArtifactStore:
    artifacts_dir = Path(settings.storage_artifacts_dir)
    return ArtifactStore(artifacts_dir)


def create_orchestrator(trace: "PipelineTrace | None" = None) -> OrchestratorProtocol:
    storage = create_storage()
    artifact_store = create_artifact_store()
    market_data_provider = create_market_data_provider()
    news_provider = create_news_provider()
    technical_analyst = create_technical_analyst()
    news_analyst = create_news_analyst()
    synthesizer = create_synthesizer()
    candles_repository = create_candles_repository()

    verifier_agent: VerifierAgent | None = None
    verification_repository: VerificationRepository | None = None
    if settings.llm_verifier_enabled:
        verifier_agent = create_verifier_agent()
        verification_repository = create_verification_repository()

    return RuntimeOrchestrator(
        storage=storage,
        artifact_store=artifact_store,
        market_data_provider=market_data_provider,
        news_provider=news_provider,
        technical_analyst=technical_analyst,
        news_analyst=news_analyst,
        synthesizer=synthesizer,
        candles_repository=candles_repository,
        verifier_agent=verifier_agent,
        verification_repository=verification_repository,
        verifier_enabled=settings.llm_verifier_enabled,
        trace=trace,
    )


def create_minute_loop(clock: Clock | None = None) -> MinuteLoop:
    if clock is None:
        clock = SystemClock()
    orchestrator = create_orchestrator()
    scheduler = Scheduler(clock)
    return MinuteLoop(orchestrator=orchestrator, scheduler=scheduler, clock=clock)
