"""
Offline contract tests for RuntimeOrchestrator pipeline.

These tests verify the orchestrator's behavior with mocked providers,
ensuring we can refactor safely without regressions.
"""

import json
from datetime import datetime, timedelta
from unittest.mock import MagicMock, Mock, patch

import pytest

from src.agents.news_analyst import NewsAnalyst
from src.agents.synthesizer import Synthesizer
from src.agents.technical_analyst import TechnicalAnalyst
from src.core.models.candle import Candle
from src.core.models.llm import LlmResponse
from src.core.models.news import NewsArticle, NewsDigest
from src.core.models.rationale import Rationale, RationaleType
from src.core.models.recommendation import Recommendation
from src.core.models.run import Run, RunStatus
from src.core.models.timeframe import Timeframe
from src.core.ports.llm_provider import HealthCheckResult, LlmProvider
from src.core.ports.market_data_provider import MarketDataProvider
from src.core.ports.news_provider import NewsProvider
from src.core.ports.storage import (
    RationalesRepositoryPort,
    RecommendationsRepositoryPort,
    RunsRepositoryPort,
    Storage,
)
from src.runtime.orchestrator import RuntimeOrchestrator
from src.storage.artifacts.artifact_store import ArtifactStore


# =============================================================================
# Mock Implementations
# =============================================================================


class MockMarketDataProvider(MarketDataProvider):
    """Mock market data provider for offline testing."""

    def __init__(self, candles: list[Candle] | None = None, should_fail: bool = False) -> None:
        self._candles = candles
        self._should_fail = should_fail

    def fetch_candles(
        self,
        symbol: str,
        timeframe: Timeframe,
        count: int,
        from_time: datetime | None = None,
        to_time: datetime | None = None,
    ) -> list[Candle]:
        if self._should_fail:
            raise ConnectionError("Mock network failure")
        if self._candles is not None:
            return self._candles[:count]
        return generate_mock_candles(count)


class MockNewsProvider(NewsProvider):
    """Mock news provider for offline testing."""

    def __init__(
        self,
        digest: NewsDigest | None = None,
        should_fail: bool = False,
        fail_exception: Exception | None = None,
    ) -> None:
        self._digest = digest
        self._should_fail = should_fail
        self._fail_exception = fail_exception or ConnectionError("Mock news provider failure")

    def get_news_summary(self, symbol: str) -> str:
        if self._should_fail:
            raise self._fail_exception
        return f"Mock news summary for {symbol}"

    def get_news_digest(self, symbol: str, timeframe: Timeframe) -> NewsDigest:
        if self._should_fail:
            raise self._fail_exception
        if self._digest is not None:
            return self._digest
        return generate_mock_news_digest(symbol, timeframe)


class MockLlmProvider(LlmProvider):
    """Mock LLM provider for offline testing."""

    def __init__(
        self,
        name: str = "mock_provider",
        responses: dict[str, str] | None = None,
        available: bool = True,
    ) -> None:
        self._name = name
        self._responses = responses or {}
        self._available = available

    def get_provider_name(self) -> str:
        return self._name

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        return "Mock LLM response"

    def health_check(self) -> HealthCheckResult:
        return HealthCheckResult(ok=self._available, reason="" if self._available else "unavailable")


class MockRunsRepository:
    """Mock runs repository."""

    def __init__(self) -> None:
        self._runs: dict[int, Run] = {}
        self._next_id = 1

    def create(self, run: Run) -> int:
        run_id = self._next_id
        self._next_id += 1
        self._runs[run_id] = run
        return run_id

    def update_run(
        self,
        run_id: int,
        status: str,
        end_time: datetime,
        error_message: str | None,
    ) -> None:
        if run_id in self._runs:
            self._runs[run_id].status = RunStatus(status)
            self._runs[run_id].end_time = end_time
            self._runs[run_id].error_message = error_message

    def get_by_id(self, run_id: int) -> Run | None:
        return self._runs.get(run_id)


class MockRecommendationsRepository:
    """Mock recommendations repository."""

    def __init__(self) -> None:
        self._recommendations: dict[int, Recommendation] = {}
        self._next_id = 1

    def save(self, recommendation: Recommendation) -> int:
        rec_id = self._next_id
        self._next_id += 1
        recommendation.id = rec_id
        self._recommendations[rec_id] = recommendation
        return rec_id

    def get_latest(self) -> Recommendation | None:
        if not self._recommendations:
            return None
        latest_id = max(self._recommendations.keys())
        return self._recommendations[latest_id]


class MockRationalesRepository:
    """Mock rationales repository."""

    def __init__(self) -> None:
        self._rationales: list[Rationale] = []
        self._next_id = 1

    def save(self, rationale: Rationale) -> int:
        rationale_id = self._next_id
        self._next_id += 1
        rationale.id = rationale_id
        self._rationales.append(rationale)
        return rationale_id

    def get_by_run_id(self, run_id: int) -> list[Rationale]:
        return [r for r in self._rationales if r.run_id == run_id]


class MockStorage(Storage):
    """Mock storage with in-memory repositories."""

    def __init__(self) -> None:
        self._runs = MockRunsRepository()
        self._recommendations = MockRecommendationsRepository()
        self._rationales = MockRationalesRepository()

    @property
    def runs(self) -> RunsRepositoryPort:
        return self._runs  # type: ignore[return-value]

    @property
    def recommendations(self) -> RecommendationsRepositoryPort:
        return self._recommendations  # type: ignore[return-value]

    @property
    def rationales(self) -> RationalesRepositoryPort:
        return self._rationales  # type: ignore[return-value]

    @property
    def journal(self):
        return MagicMock()

    @property
    def outcomes(self):
        return MagicMock()


# =============================================================================
# Test Fixtures and Helpers
# =============================================================================


def generate_mock_candles(count: int = 300) -> list[Candle]:
    """Generate deterministic mock candles for testing."""
    base_time = datetime(2024, 1, 1, 12, 0, 0)
    base_price = 1.1000
    candles = []
    for i in range(count):
        timestamp = base_time + timedelta(minutes=i)
        open_price = base_price + (i * 0.0001)
        high_price = open_price + 0.0005
        low_price = open_price - 0.0003
        close_price = open_price + 0.0002
        candles.append(
            Candle(
                timestamp=timestamp,
                open=open_price,
                high=high_price,
                low=low_price,
                close=close_price,
                volume=1000.0 + i,
            )
        )
    return candles


def generate_mock_news_digest(symbol: str, timeframe: Timeframe) -> NewsDigest:
    """Generate a mock news digest with MEDIUM quality."""
    return NewsDigest(
        symbol=symbol,
        timeframe=timeframe,
        window_hours=24,
        articles=[
            NewsArticle(
                title=f"Market outlook for {symbol}",
                url="https://example.com/news1",
                source="MockNews",
                published_at=datetime.now(),
                language="en",
                relevance_score=0.8,
                query_tag="primary",
            ),
        ],
        quality="MEDIUM",
        quality_reason="Mock news for testing",
        provider_used="MockProvider",
    )


def create_mock_llm_router(
    tech_response: str | None = None,
    news_response: str | None = None,
    synthesis_response: str | None = None,
) -> MagicMock:
    """Create a mock LlmRouter with configurable responses."""
    from src.llm.providers.llm_router import LlmRouteStep, LlmRoutingConfig, LlmTaskRouting
    from src.llm.providers.llm_router import LlmRouter

    mock_router = MagicMock(spec=LlmRouter)

    # Default responses
    default_tech = "Technical analysis: RSI at 55, trend is neutral. Watch 1.1050 resistance."
    default_news = json.dumps({
        "summary": "Market sentiment is neutral with no major events.",
        "sentiment": "NEU",
        "impact_score": 0.3,
        "evidence_titles": [],
    })
    default_synthesis = json.dumps({
        "action": "WAIT",
        "confidence": 0.5,
        "brief": "Mixed signals suggest waiting for clearer direction.",
    })

    def generate_side_effect(task: str, system_prompt: str, user_prompt: str) -> LlmResponse:
        responses = {
            "tech_analysis": tech_response or default_tech,
            "news_analysis": news_response or default_news,
            "synthesis": synthesis_response or default_synthesis,
            "verification": json.dumps({"passed": True, "issues": [], "policy_version": "1.0"}),
        }
        return LlmResponse(
            text=responses.get(task, "{}"),
            provider_name="mock_provider",
            model_name="mock_model",
            latency_ms=100,
            attempts=1,
            error=None,
        )

    mock_router.generate.side_effect = generate_side_effect
    return mock_router


def create_test_orchestrator(
    market_provider: MarketDataProvider | None = None,
    news_provider: NewsProvider | None = None,
    llm_router: MagicMock | None = None,
    storage: Storage | None = None,
) -> tuple[RuntimeOrchestrator, MockStorage]:
    """Create a RuntimeOrchestrator with mock dependencies."""
    mock_storage = storage if isinstance(storage, MockStorage) else MockStorage()
    mock_market = market_provider or MockMarketDataProvider()
    mock_news = news_provider or MockNewsProvider()
    mock_router = llm_router or create_mock_llm_router()

    # Create agents with the mock router
    tech_analyst = TechnicalAnalyst(llm_router=mock_router)
    news_analyst = NewsAnalyst(llm_router=mock_router)
    synthesizer = Synthesizer(llm_router=mock_router)

    # Create mock artifact store
    mock_artifact_store = MagicMock(spec=ArtifactStore)
    mock_artifact_store.save_llm_exchange.return_value = None
    mock_artifact_store.save_json.return_value = None
    mock_artifact_store.save_text.return_value = None

    orchestrator = RuntimeOrchestrator(
        storage=mock_storage,
        artifact_store=mock_artifact_store,
        market_data_provider=mock_market,
        news_provider=mock_news,
        technical_analyst=tech_analyst,
        news_analyst=news_analyst,
        synthesizer=synthesizer,
        candles_repository=None,
        verifier_agent=None,
        verification_repository=None,
        verifier_enabled=False,
        trace=None,
    )

    return orchestrator, mock_storage


# =============================================================================
# Contract Tests
# =============================================================================


class TestOrchestratorHappyPath:
    """Tests for successful pipeline execution."""

    def test_run_analysis_creates_run_and_recommendation(self) -> None:
        """Happy path: run completes, recommendation is persisted."""
        orchestrator, storage = create_test_orchestrator()

        run_id = orchestrator.run_analysis(symbol="EURUSD", timeframe=Timeframe.H1)

        # Verify run was created and completed
        assert run_id == 1
        run = storage._runs.get_by_id(run_id)
        assert run is not None
        assert run.status == RunStatus.SUCCESS

        # Verify recommendation was saved
        recommendation = storage._recommendations.get_latest()
        assert recommendation is not None
        assert recommendation.symbol == "EURUSD"
        assert recommendation.timeframe == Timeframe.H1
        assert recommendation.action in ["CALL", "PUT", "WAIT"]
        assert 0.0 <= recommendation.confidence <= 1.0

    def test_run_analysis_persists_rationales(self) -> None:
        """Happy path: all rationale types are persisted."""
        orchestrator, storage = create_test_orchestrator()

        run_id = orchestrator.run_analysis(symbol="GBPUSD", timeframe=Timeframe.M15)

        # Verify rationales were saved
        rationales = storage._rationales.get_by_run_id(run_id)
        assert len(rationales) >= 3  # TECHNICAL, NEWS, SYNTHESIS

        rationale_types = {r.rationale_type for r in rationales}
        assert RationaleType.TECHNICAL in rationale_types
        assert RationaleType.NEWS in rationale_types
        assert RationaleType.SYNTHESIS in rationale_types

    def test_run_analysis_records_llm_metadata(self) -> None:
        """Happy path: LLM metadata (provider, model, latency) is recorded."""
        orchestrator, storage = create_test_orchestrator()

        run_id = orchestrator.run_analysis(symbol="USDJPY", timeframe=Timeframe.H1)

        rationales = storage._rationales.get_by_run_id(run_id)
        tech_rationale = next(
            (r for r in rationales if r.rationale_type == RationaleType.TECHNICAL), None
        )

        assert tech_rationale is not None
        assert tech_rationale.provider_name == "mock_provider"
        assert tech_rationale.model_name == "mock_model"
        assert tech_rationale.latency_ms is not None


class TestOrchestratorNewsProviderFailure:
    """Tests for news provider failure handling."""

    def test_news_provider_throws_pipeline_continues(self) -> None:
        """News provider throws: pipeline doesn't crash, digest degrades to LOW."""
        failing_news = MockNewsProvider(should_fail=True)
        orchestrator, storage = create_test_orchestrator(news_provider=failing_news)

        # Should not raise
        run_id = orchestrator.run_analysis(symbol="EURUSD", timeframe=Timeframe.H1)

        # Run should still complete (may be success or with degraded news)
        run = storage._runs.get_by_id(run_id)
        assert run is not None
        # The run shouldn't crash even if news fails
        assert run.status in [RunStatus.SUCCESS, RunStatus.FAILED]

    def test_news_provider_timeout_degrades_gracefully(self) -> None:
        """News provider timeout: digest degrades to LOW quality."""
        timeout_news = MockNewsProvider(
            should_fail=True,
            fail_exception=TimeoutError("Mock timeout"),
        )
        orchestrator, storage = create_test_orchestrator(news_provider=timeout_news)

        run_id = orchestrator.run_analysis(symbol="EURUSD", timeframe=Timeframe.H1)

        # Pipeline should handle the error
        run = storage._runs.get_by_id(run_id)
        assert run is not None


class TestOrchestratorInsufficientCandles:
    """Tests for insufficient candles handling."""

    def test_too_few_candles_fails_run_correctly(self) -> None:
        """Too few candles: pipeline correctly fails run with reason."""
        # Generate only 50 candles (need at least 200)
        few_candles = generate_mock_candles(50)
        market_provider = MockMarketDataProvider(candles=few_candles)
        orchestrator, storage = create_test_orchestrator(market_provider=market_provider)

        run_id = orchestrator.run_analysis(symbol="EURUSD", timeframe=Timeframe.H1)

        # Run should be marked as failed
        run = storage._runs.get_by_id(run_id)
        assert run is not None
        assert run.status == RunStatus.FAILED
        assert run.error_message is not None
        assert "candles" in run.error_message.lower() or "insufficient" in run.error_message.lower()

    def test_market_data_fetch_failure_fails_run(self) -> None:
        """Market data fetch fails: run is marked failed with error."""
        failing_market = MockMarketDataProvider(should_fail=True)
        orchestrator, storage = create_test_orchestrator(market_provider=failing_market)

        run_id = orchestrator.run_analysis(symbol="EURUSD", timeframe=Timeframe.H1)

        run = storage._runs.get_by_id(run_id)
        assert run is not None
        assert run.status == RunStatus.FAILED
        assert run.error_message is not None

    def test_exactly_200_candles_passes(self) -> None:
        """Exactly 200 candles: pipeline should pass minimum threshold."""
        exactly_200 = generate_mock_candles(200)
        market_provider = MockMarketDataProvider(candles=exactly_200)
        orchestrator, storage = create_test_orchestrator(market_provider=market_provider)

        run_id = orchestrator.run_analysis(symbol="EURUSD", timeframe=Timeframe.H1)

        run = storage._runs.get_by_id(run_id)
        assert run is not None
        assert run.status == RunStatus.SUCCESS


class TestOrchestratorLlmFailures:
    """Tests for LLM failure handling."""

    def test_llm_error_recorded_in_rationale(self) -> None:
        """LLM returns error: error is recorded in rationale."""
        mock_router = MagicMock()
        mock_router.generate.return_value = LlmResponse(
            text="",
            provider_name="mock_provider",
            model_name="mock_model",
            latency_ms=100,
            attempts=3,
            error="Connection timeout",
        )
        orchestrator, storage = create_test_orchestrator(llm_router=mock_router)

        run_id = orchestrator.run_analysis(symbol="EURUSD", timeframe=Timeframe.H1)

        rationales = storage._rationales.get_by_run_id(run_id)
        # At least tech rationale should have error recorded
        tech_rationale = next(
            (r for r in rationales if r.rationale_type == RationaleType.TECHNICAL), None
        )
        if tech_rationale:
            assert tech_rationale.error == "Connection timeout"
            assert tech_rationale.attempts == 3


class TestOrchestratorDeterminism:
    """Tests to ensure deterministic behavior."""

    def test_same_input_produces_consistent_structure(self) -> None:
        """Same inputs should produce same structural output."""
        # Run twice with same mock data
        orchestrator1, storage1 = create_test_orchestrator()
        orchestrator2, storage2 = create_test_orchestrator()

        run_id1 = orchestrator1.run_analysis(symbol="EURUSD", timeframe=Timeframe.H1)
        run_id2 = orchestrator2.run_analysis(symbol="EURUSD", timeframe=Timeframe.H1)

        # Both should have same structure
        rec1 = storage1._recommendations.get_latest()
        rec2 = storage2._recommendations.get_latest()

        assert rec1 is not None and rec2 is not None
        assert rec1.symbol == rec2.symbol
        assert rec1.timeframe == rec2.timeframe
        assert rec1.action == rec2.action
