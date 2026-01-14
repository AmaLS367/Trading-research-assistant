from datetime import datetime, timedelta
from unittest.mock import Mock

from src.core.models.candle import Candle
from src.core.models.news import NewsDigest
from src.core.models.rationale import RationaleType
from src.core.models.recommendation import Recommendation
from src.core.models.timeframe import Timeframe
from src.runtime.jobs.run_agents_job import RunAgentsJob


def test_synthesis_content_includes_system_note_for_low_quality() -> None:
    market_data_provider = Mock()
    base_time = datetime(2024, 1, 1, 12, 0, 0)
    test_candles = [
        Candle(
            timestamp=base_time + timedelta(hours=i),
            open=1.0 + i * 0.001,
            high=1.1 + i * 0.001,
            low=0.9 + i * 0.001,
            close=1.05 + i * 0.001,
            volume=1000.0,
        )
        for i in range(200)
    ]
    market_data_provider.fetch_candles.return_value = test_candles

    news_provider = Mock()
    news_digest = NewsDigest(
        symbol="EURUSD",
        timeframe=Timeframe.H1,
        window_hours=24,
        articles=[],
        quality="LOW",
        quality_reason="Insufficient articles",
    )
    news_provider.get_news_digest.return_value = news_digest

    news_analyst = Mock()
    news_analyst.analyze.return_value = news_digest

    technical_analyst = Mock()
    technical_analyst.analyze.return_value = "Technical view: bullish"

    synthesizer = Mock()
    synthesizer.synthesize.return_value = (
        Recommendation(
            symbol="EURUSD",
            timestamp=datetime.now(),
            timeframe=Timeframe.H1,
            action="CALL",
            brief="Strong bullish momentum detected.",
            confidence=0.75,
        ),
        {"parse_ok": True, "parse_error": None, "raw_output": "", "retry_used": False, "retry_raw_output": None, "brief_warning": None},
    )

    recommendations_repo = Mock()
    recommendations_repo.save.return_value = 1

    runs_repo = Mock()
    runs_repo.create.return_value = 1

    rationales_repo = Mock()

    job = RunAgentsJob(
        market_data_provider=market_data_provider,
        news_provider=news_provider,
        technical_analyst=technical_analyst,
        synthesizer=synthesizer,
        news_analyst=news_analyst,
        recommendations_repository=recommendations_repo,
        runs_repository=runs_repo,
        rationales_repository=rationales_repo,
    )

    job.run(symbol="EURUSD", timeframe=Timeframe.H1, count=200)

    synthesis_calls = [call for call in rationales_repo.save.call_args_list if call[0][0].rationale_type == RationaleType.SYNTHESIS]
    assert len(synthesis_calls) == 1

    saved_rationale = synthesis_calls[0][0][0]
    assert "[System Note: News ignored due to LOW quality]" in saved_rationale.content
    assert "Strong bullish momentum detected." in saved_rationale.content


def test_synthesis_content_no_system_note_for_medium_quality() -> None:
    market_data_provider = Mock()
    base_time = datetime(2024, 1, 1, 12, 0, 0)
    test_candles = [
        Candle(
            timestamp=base_time + timedelta(hours=i),
            open=1.0 + i * 0.001,
            high=1.1 + i * 0.001,
            low=0.9 + i * 0.001,
            close=1.05 + i * 0.001,
            volume=1000.0,
        )
        for i in range(200)
    ]
    market_data_provider.fetch_candles.return_value = test_candles

    news_provider = Mock()
    news_digest = NewsDigest(
        symbol="EURUSD",
        timeframe=Timeframe.H1,
        window_hours=24,
        articles=[],
        quality="MEDIUM",
        quality_reason="Moderate article count",
    )
    news_provider.get_news_digest.return_value = news_digest

    news_analyst = Mock()
    news_analyst.analyze.return_value = news_digest

    technical_analyst = Mock()
    technical_analyst.analyze.return_value = "Technical view: bullish"

    synthesizer = Mock()
    synthesizer.synthesize.return_value = (
        Recommendation(
            symbol="EURUSD",
            timestamp=datetime.now(),
            timeframe=Timeframe.H1,
            action="CALL",
            brief="Bullish trend with moderate news support.",
            confidence=0.70,
        ),
        {"parse_ok": True, "parse_error": None, "raw_output": "", "retry_used": False, "retry_raw_output": None, "brief_warning": None},
    )

    recommendations_repo = Mock()
    recommendations_repo.save.return_value = 1

    runs_repo = Mock()
    runs_repo.create.return_value = 1

    rationales_repo = Mock()

    job = RunAgentsJob(
        market_data_provider=market_data_provider,
        news_provider=news_provider,
        technical_analyst=technical_analyst,
        synthesizer=synthesizer,
        news_analyst=news_analyst,
        recommendations_repository=recommendations_repo,
        runs_repository=runs_repo,
        rationales_repository=rationales_repo,
    )

    job.run(symbol="EURUSD", timeframe=Timeframe.H1, count=200)

    synthesis_calls = [call for call in rationales_repo.save.call_args_list if call[0][0].rationale_type == RationaleType.SYNTHESIS]
    assert len(synthesis_calls) == 1

    saved_rationale = synthesis_calls[0][0][0]
    assert "[System Note: News ignored due to LOW quality]" not in saved_rationale.content
    assert "Bullish trend with moderate news support." in saved_rationale.content


def test_synthesis_content_no_system_note_for_high_quality() -> None:
    market_data_provider = Mock()
    base_time = datetime(2024, 1, 1, 12, 0, 0)
    test_candles = [
        Candle(
            timestamp=base_time + timedelta(hours=i),
            open=1.0 + i * 0.001,
            high=1.1 + i * 0.001,
            low=0.9 + i * 0.001,
            close=1.05 + i * 0.001,
            volume=1000.0,
        )
        for i in range(200)
    ]
    market_data_provider.fetch_candles.return_value = test_candles

    news_provider = Mock()
    news_digest = NewsDigest(
        symbol="EURUSD",
        timeframe=Timeframe.H1,
        window_hours=24,
        articles=[],
        quality="HIGH",
        quality_reason="High quality articles",
    )
    news_provider.get_news_digest.return_value = news_digest

    news_analyst = Mock()
    news_analyst.analyze.return_value = news_digest

    technical_analyst = Mock()
    technical_analyst.analyze.return_value = "Technical view: bullish"

    synthesizer = Mock()
    synthesizer.synthesize.return_value = (
        Recommendation(
            symbol="EURUSD",
            timestamp=datetime.now(),
            timeframe=Timeframe.H1,
            action="CALL",
            brief="Strong bullish signals with positive news sentiment.",
            confidence=0.85,
        ),
        {"parse_ok": True, "parse_error": None, "raw_output": "", "retry_used": False, "retry_raw_output": None, "brief_warning": None},
    )

    recommendations_repo = Mock()
    recommendations_repo.save.return_value = 1

    runs_repo = Mock()
    runs_repo.create.return_value = 1

    rationales_repo = Mock()

    job = RunAgentsJob(
        market_data_provider=market_data_provider,
        news_provider=news_provider,
        technical_analyst=technical_analyst,
        synthesizer=synthesizer,
        news_analyst=news_analyst,
        recommendations_repository=recommendations_repo,
        runs_repository=runs_repo,
        rationales_repository=rationales_repo,
    )

    job.run(symbol="EURUSD", timeframe=Timeframe.H1, count=200)

    synthesis_calls = [call for call in rationales_repo.save.call_args_list if call[0][0].rationale_type == RationaleType.SYNTHESIS]
    assert len(synthesis_calls) == 1

    saved_rationale = synthesis_calls[0][0][0]
    assert "[System Note: News ignored due to LOW quality]" not in saved_rationale.content
    assert "Strong bullish signals with positive news sentiment." in saved_rationale.content
