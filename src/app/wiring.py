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
from src.runtime.config import RuntimeConfig
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


def create_runtime_config() -> RuntimeConfig:
    """Create RuntimeConfig from application settings."""
    # Collect per-task timeouts
    task_timeouts: dict[str, float] = {}
    for prefix in ["tech", "news", "synthesis", "verifier"]:
        timeout_attr = f"{prefix}_timeout_seconds"
        timeout_value = getattr(settings, timeout_attr, None)
        if timeout_value is not None and isinstance(timeout_value, (int, float)):
            task_timeouts[f"{prefix}_timeout_seconds"] = float(timeout_value)

    return RuntimeConfig(
        market_data_window_candles=settings.runtime_market_data_window_candles,
        llm_enabled=settings.runtime_llm_enabled,
        llm_timeout_seconds=settings.llm_timeout_seconds,
        task_timeouts=task_timeouts,
        verifier_enabled=settings.llm_verifier_enabled,
        verifier_mode=settings.llm_verifier_mode,
        verifier_max_repairs=settings.llm_verifier_max_repairs,
        mvp_timeframe=settings.runtime_mvp_timeframe,
        mvp_symbols=settings.mvp_symbols(),
    )


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

    if settings.ollama_server_enabled:
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
    from src.llm.providers.llm_router import (
        LastResortConfig,
        LlmRouteStep,
        LlmRoutingConfig,
        LlmTaskRouting,
        TaskOverrides,
    )

    providers = create_llm_providers()

    # Build routing config
    routing_config = LlmRoutingConfig(
        router_mode=settings.llm_router_mode,
        verifier_enabled=settings.llm_verifier_enabled,
        max_retries=settings.llm_max_retries,
        timeout_seconds=settings.llm_timeout_seconds,
        temperature=settings.llm_temperature,
    )

    # Build task routings
    task_routings: dict[str, LlmTaskRouting] = {}
    for task_name in [TASK_TECH_ANALYSIS, TASK_NEWS_ANALYSIS, TASK_SYNTHESIS, TASK_VERIFICATION]:
        candidates = settings.get_task_candidates(task_name)
        if not candidates:
            steps = [
                LlmRouteStep(
                    provider=PROVIDER_OLLAMA_LOCAL,
                    model=settings.ollama_model or "llama3:latest",
                )
            ]
        else:
            steps = [LlmRouteStep(provider=c.provider, model=c.model) for c in candidates]
        task_routings[task_name] = LlmTaskRouting(steps=steps)

    # Build last resort config
    last_resort = LastResortConfig(
        provider=settings.llm_last_resort.provider,
        model=settings.llm_last_resort.model,
    )

    # Build provider timeouts
    provider_timeouts: dict[str, float] = {}
    for provider_prefix in ["ollama_local", "ollama_server", "deepseek_api"]:
        # Per-provider timeout
        timeout_attr = f"{provider_prefix}_timeout_seconds"
        timeout_val = getattr(settings, timeout_attr, None)
        if timeout_val is not None and isinstance(timeout_val, (int, float)):
            provider_timeouts[f"{provider_prefix}_timeout_seconds"] = float(timeout_val)

        # Per-provider-per-task timeouts
        for task_prefix in ["tech", "news", "synthesis", "verifier"]:
            task_timeout_attr = f"{provider_prefix}_{task_prefix}_timeout_seconds"
            task_timeout_val = getattr(settings, task_timeout_attr, None)
            if task_timeout_val is not None and isinstance(task_timeout_val, (int, float)):
                provider_timeouts[f"{provider_prefix}_{task_prefix}_timeout_seconds"] = float(task_timeout_val)

    # Build task overrides
    task_overrides: dict[str, TaskOverrides] = {}
    task_prefix_map = {
        TASK_TECH_ANALYSIS: "tech",
        TASK_NEWS_ANALYSIS: "news",
        TASK_SYNTHESIS: "synthesis",
        TASK_VERIFICATION: "verifier",
    }
    for task_name, prefix in task_prefix_map.items():
        timeout_val = getattr(settings, f"{prefix}_timeout_seconds", None)
        temp_val = getattr(settings, f"{prefix}_temperature", None)
        if timeout_val is not None or temp_val is not None:
            task_overrides[task_name] = TaskOverrides(
                timeout_seconds=float(timeout_val) if timeout_val is not None else None,
                temperature=float(temp_val) if temp_val is not None else None,
            )

    return LlmRouter(
        providers=providers,
        routing_config=routing_config,
        task_routings=task_routings,
        last_resort=last_resort,
        provider_timeouts=provider_timeouts,
        task_overrides=task_overrides,
    )


# Singleton LLM router instance
_llm_router: LlmRouter | None = None


def get_llm_router() -> LlmRouter:
    """Get the singleton LLM router instance."""
    global _llm_router
    if _llm_router is None:
        _llm_router = create_llm_router()
    return _llm_router


def create_technical_analyst() -> TechnicalAnalyst:
    return TechnicalAnalyst(llm_router=get_llm_router())


def create_synthesizer() -> Synthesizer:
    return Synthesizer(llm_router=get_llm_router())


def create_news_analyst() -> NewsAnalyst:
    return NewsAnalyst(llm_router=get_llm_router())


def create_verifier_agent() -> VerifierAgent:
    return VerifierAgent(llm_router=get_llm_router())


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
    runtime_config = create_runtime_config()

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
        config=runtime_config,
    )


def create_minute_loop(clock: Clock | None = None) -> MinuteLoop:
    if clock is None:
        clock = SystemClock()
    orchestrator = create_orchestrator()
    scheduler = Scheduler(clock)
    runtime_config = create_runtime_config()
    return MinuteLoop(orchestrator=orchestrator, scheduler=scheduler, clock=clock, config=runtime_config)
