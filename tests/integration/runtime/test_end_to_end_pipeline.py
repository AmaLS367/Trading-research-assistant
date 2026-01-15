import tempfile
from datetime import datetime
from pathlib import Path

from src.core.models.candle import Candle
from src.core.models.news import NewsDigest
from src.core.models.timeframe import Timeframe
from src.core.ports.llm_provider import HealthCheckResult, LlmProvider
from src.core.ports.market_data_provider import MarketDataProvider
from src.core.ports.news_provider import NewsProvider
from src.runtime.orchestrator import RuntimeOrchestrator
from src.storage.artifacts.artifact_store import ArtifactStore
from src.storage.sqlite.connection import DBConnection
from src.storage.sqlite.storage import SqliteStorage


class MockLlmProvider(LlmProvider):
    def __init__(self, provider_name: str, model_name: str, should_fail: bool = False) -> None:
        self.provider_name = provider_name
        self.model_name = model_name
        self.should_fail = should_fail

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        if self.should_fail:
            raise ValueError("Mock provider failure")
        return f"Mock response from {self.provider_name}"

    def health_check(self) -> HealthCheckResult:
        return HealthCheckResult(ok=not self.should_fail, reason="mock")

    def get_provider_name(self) -> str:
        return self.provider_name


class MockMarketDataProvider(MarketDataProvider):
    def fetch_candles(self, symbol: str, timeframe: Timeframe, count: int) -> list[Candle]:
        candles: list[Candle] = []
        base_time = datetime(2024, 1, 1, 12, 0, 0)
        for i in range(count):
            candles.append(
                Candle(
                    timestamp=base_time,
                    open=1.1000 + i * 0.0001,
                    high=1.1005 + i * 0.0001,
                    low=1.0995 + i * 0.0001,
                    close=1.1002 + i * 0.0001,
                    volume=1000.0,
                )
            )
        return candles


class MockNewsProvider(NewsProvider):
    def fetch_news(self, symbol: str, timeframe: Timeframe, window_hours: int) -> NewsDigest:
        return NewsDigest(
            symbol=symbol,
            timeframe=timeframe,
            window_hours=window_hours,
            articles=[],
            quality="LOW",
            quality_reason="Mock provider",
        )


def test_end_to_end_pipeline_offline():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        artifacts_dir = Path(tmpdir) / "artifacts"

        db = DBConnection(str(db_path))
        db.run_migration("src/storage/sqlite/migrations")

        storage = SqliteStorage(db)
        artifact_store = ArtifactStore(artifacts_dir)

        mock_tech_provider = MockLlmProvider("test_provider", "test_model")
        mock_news_provider_llm = MockLlmProvider("test_provider", "test_model")
        mock_synth_provider = MockLlmProvider("test_provider", "test_model")

        from src.agents.news_analyst import NewsAnalyst
        from src.agents.synthesizer import Synthesizer
        from src.agents.technical_analyst import TechnicalAnalyst
        from src.agents.verifier import VerifierAgent
        from src.app.settings import LlmRouteStep, LlmRoutingConfig, LlmTaskRouting
        from src.core.models.llm import LlmResponse
        from src.core.ports.llm_tasks import (
            TASK_NEWS_ANALYSIS,
            TASK_SYNTHESIS,
            TASK_TECH_ANALYSIS,
            TASK_VERIFICATION,
        )
        from src.llm.providers.llm_router import LlmRouter

        providers: dict[str, LlmProvider] = {"test_provider": mock_tech_provider}
        routing_config = LlmRoutingConfig(
            router_mode="sequential",
            verifier_enabled=True,
            max_retries=1,
            timeout_seconds=60.0,
            temperature=0.2,
        )

        task_routings: dict[str, LlmTaskRouting] = {
            TASK_TECH_ANALYSIS: LlmTaskRouting(
                steps=[LlmRouteStep(provider="test_provider", model="test_model")]
            ),
            TASK_NEWS_ANALYSIS: LlmTaskRouting(
                steps=[LlmRouteStep(provider="test_provider", model="test_model")]
            ),
            TASK_SYNTHESIS: LlmTaskRouting(
                steps=[LlmRouteStep(provider="test_provider", model="test_model")]
            ),
            TASK_VERIFICATION: LlmTaskRouting(
                steps=[LlmRouteStep(provider="test_provider", model="test_model")]
            ),
        }

        router = LlmRouter(providers, routing_config, task_routings)

        def mock_generate(task, system_prompt, user_prompt):
            if task == TASK_VERIFICATION:
                return LlmResponse(
                    text='{"passed": true, "issues": [], "suggested_fix": null, "policy_version": "1.0"}',
                    provider_name="test_provider",
                    model_name="test_model",
                    latency_ms=50,
                    attempts=1,
                    error=None,
                )
            elif task == TASK_SYNTHESIS:
                return LlmResponse(
                    text='{"action": "CALL", "confidence": 0.75, "brief": "Test recommendation"}',
                    provider_name="test_provider",
                    model_name="test_model",
                    latency_ms=100,
                    attempts=1,
                    error=None,
                )
            else:
                return LlmResponse(
                    text="Test analysis",
                    provider_name="test_provider",
                    model_name="test_model",
                    latency_ms=80,
                    attempts=1,
                    error=None,
                )

        router.generate = mock_generate

        technical_analyst = TechnicalAnalyst(router)
        news_analyst = NewsAnalyst(router)
        synthesizer = Synthesizer(router)
        verifier = VerifierAgent(router)

        from src.storage.sqlite.repositories.verification_repository import (
            VerificationRepository,
        )

        verification_repo = VerificationRepository(db)

        orchestrator = RuntimeOrchestrator(
            storage=storage,
            artifact_store=artifact_store,
            market_data_provider=MockMarketDataProvider(),
            news_provider=MockNewsProvider(),
            technical_analyst=technical_analyst,
            news_analyst=news_analyst,
            synthesizer=synthesizer,
            candles_repository=None,
            verifier_agent=verifier,
            verification_repository=verification_repo,
        )

        run_id = orchestrator.run_analysis("EURUSD", Timeframe.H1)

        assert run_id > 0

        recommendation = storage.recommendations.get_latest()
        assert recommendation is not None
        assert recommendation.symbol == "EURUSD"
        assert recommendation.timeframe == Timeframe.H1

        rationales = storage.rationales.get_by_run_id(run_id)
        assert len(rationales) >= 3

        verification_report = verification_repo.get_latest_by_run_id(run_id)
        assert verification_report is not None
        assert verification_report.passed is True

        run_dir = artifacts_dir / f"run_{run_id}"
        assert run_dir.exists()

        llm_dir = run_dir / "llm"
        assert llm_dir.exists()
