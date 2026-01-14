from pathlib import Path

from src.agents.news_analyst import NewsAnalyst
from src.agents.synthesizer import Synthesizer
from src.agents.technical_analyst import TechnicalAnalyst
from src.app.settings import settings
from src.core.ports.llm_provider import LlmProvider
from src.core.ports.market_data_provider import MarketDataProvider
from src.core.ports.news_provider import NewsProvider
from src.core.ports.orchestrator import OrchestratorProtocol
from src.core.ports.storage import Storage
from src.data_providers.forex.fallback_provider import FallbackMarketDataProvider
from src.data_providers.forex.oanda_provider import OandaProvider
from src.data_providers.forex.twelve_data_provider import TwelveDataProvider
from src.llm.ollama.ollama_client import OllamaClient
from src.news_providers.gdelt_provider import GDELTProvider
from src.news_providers.multi_news_provider import MultiNewsProvider
from src.news_providers.newsapi_provider import NewsAPIProvider
from src.runtime.orchestrator import RuntimeOrchestrator
from src.storage.artifacts.artifact_store import ArtifactStore
from src.storage.sqlite.connection import DBConnection
from src.storage.sqlite.repositories.rationales_repository import RationalesRepository
from src.storage.sqlite.repositories.recommendations_repository import RecommendationsRepository
from src.storage.sqlite.repositories.runs_repository import RunsRepository
from src.storage.sqlite.storage import SqliteStorage


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


def create_llm_provider() -> LlmProvider:
    if not settings.ollama_model:
        raise ValueError("OLLAMA_MODEL must be set in environment variables")
    return OllamaClient(
        base_url=settings.ollama_base_url,
        model=settings.ollama_model,
    )


def create_technical_analyst() -> TechnicalAnalyst:
    llm_provider = create_llm_provider()
    return TechnicalAnalyst(llm_provider=llm_provider)


def create_synthesizer() -> Synthesizer:
    llm_provider = create_llm_provider()
    return Synthesizer(llm_provider=llm_provider)


def create_news_analyst() -> NewsAnalyst:
    llm_provider = create_llm_provider()
    return NewsAnalyst(llm_provider=llm_provider)


def create_recommendations_repository() -> RecommendationsRepository:
    db = DBConnection(str(settings.storage_sqlite_db_path))
    return RecommendationsRepository(db)


def create_runs_repository() -> RunsRepository:
    db = DBConnection(str(settings.storage_sqlite_db_path))
    return RunsRepository(db)


def create_rationales_repository() -> RationalesRepository:
    db = DBConnection(str(settings.storage_sqlite_db_path))
    return RationalesRepository(db)


def create_storage() -> Storage:
    db = DBConnection(str(settings.storage_sqlite_db_path))
    return SqliteStorage(db)


def create_artifact_store() -> ArtifactStore:
    artifacts_dir = Path(settings.storage_artifacts_dir)
    return ArtifactStore(artifacts_dir)


def create_orchestrator() -> OrchestratorProtocol:
    storage = create_storage()
    artifact_store = create_artifact_store()
    market_data_provider = create_market_data_provider()
    news_provider = create_news_provider()
    technical_analyst = create_technical_analyst()
    news_analyst = create_news_analyst()
    synthesizer = create_synthesizer()
    return RuntimeOrchestrator(
        storage=storage,
        artifact_store=artifact_store,
        market_data_provider=market_data_provider,
        news_provider=news_provider,
        technical_analyst=technical_analyst,
        news_analyst=news_analyst,
        synthesizer=synthesizer,
    )
