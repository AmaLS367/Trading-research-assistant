from src.agents.synthesizer import Synthesizer
from src.agents.technical_analyst import TechnicalAnalyst
from src.app.settings import settings
from src.core.ports.llm_provider import LlmProvider
from src.core.ports.market_data_provider import MarketDataProvider
from src.core.ports.news_provider import NewsProvider
from src.data_providers.forex.oanda_provider import OandaProvider
from src.llm.ollama.ollama_client import OllamaClient
from src.news_providers.gdelt_provider import GDELTProvider
from src.storage.sqlite.connection import DBConnection
from src.storage.sqlite.repositories.recommendations_repository import RecommendationsRepository


def create_market_data_provider() -> MarketDataProvider:
    return OandaProvider(
        api_key=settings.oanda_api_key,
        base_url=settings.oanda_base_url,
    )


def create_news_provider() -> NewsProvider:
    return GDELTProvider(base_url=settings.gdelt_base_url)


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


def create_recommendations_repository() -> RecommendationsRepository:
    db = DBConnection(str(settings.storage_sqlite_db_path))
    return RecommendationsRepository(db)
