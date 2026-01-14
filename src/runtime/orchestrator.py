import json
from datetime import datetime

from src.agents.news_analyst import NewsAnalyst
from src.agents.synthesizer import Synthesizer
from src.agents.technical_analyst import TechnicalAnalyst
from src.core.models.rationale import Rationale, RationaleType
from src.core.models.run import Run, RunStatus
from src.core.models.timeframe import Timeframe
from src.core.ports.market_data_provider import MarketDataProvider
from src.core.ports.news_provider import NewsProvider
from src.core.ports.storage import Storage
from src.runtime.jobs.build_features_job import BuildFeaturesJob
from src.runtime.jobs.fetch_market_data_job import FetchMarketDataJob
from src.runtime.jobs.fetch_news_job import FetchNewsJob
from src.runtime.jobs.persist_recommendation_job import PersistRecommendationJob
from src.storage.artifacts.artifact_store import ArtifactStore


class RuntimeOrchestrator:
    def __init__(
        self,
        storage: Storage,
        artifact_store: ArtifactStore,
        market_data_provider: MarketDataProvider,
        news_provider: NewsProvider,
        technical_analyst: TechnicalAnalyst,
        news_analyst: NewsAnalyst,
        synthesizer: Synthesizer,
    ) -> None:
        self.storage = storage
        self.artifact_store = artifact_store
        self.market_data_provider = market_data_provider
        self.news_provider = news_provider
        self.technical_analyst = technical_analyst
        self.news_analyst = news_analyst
        self.synthesizer = synthesizer

    def run_analysis(self, symbol: str, timeframe: Timeframe) -> int:
        run = Run(
            symbol=symbol,
            timeframe=timeframe,
            start_time=datetime.now(),
            status=RunStatus.PENDING,
        )
        run_id = self.storage.runs.create(run)

        try:
            fetch_market_data_job = FetchMarketDataJob(self.market_data_provider)
            market_result = fetch_market_data_job.run(
                symbol=symbol,
                timeframe=timeframe,
                count=300,
            )
            if not market_result.ok:
                self._mark_run_failed(run_id, market_result.error)
                return run_id

            candles = market_result.value
            if candles is None:
                self._mark_run_failed(run_id, "No candles returned from market data job")
                return run_id

            build_features_job = BuildFeaturesJob()
            features_result = build_features_job.run(
                symbol=symbol,
                timeframe=timeframe,
                candles=candles,
            )
            if not features_result.ok:
                self._mark_run_failed(run_id, features_result.error)
                return run_id

            features_value = features_result.value
            if features_value is None:
                self._mark_run_failed(
                    run_id,
                    "No snapshot or signal returned from build features job",
                )
                return run_id

            snapshot, signal = features_value

            technical_view = self.technical_analyst.analyze(snapshot, symbol, timeframe)
            technical_rationale = Rationale(
                run_id=run_id,
                rationale_type=RationaleType.TECHNICAL,
                content=technical_view,
                raw_data=None,
            )

            fetch_news_job = FetchNewsJob(self.news_provider)
            news_result = fetch_news_job.run(symbol=symbol, timeframe=timeframe)
            if not news_result.ok:
                self._mark_run_failed(run_id, news_result.error)
                return run_id

            news_digest = news_result.value
            if news_digest is None:
                self._mark_run_failed(run_id, "No news digest returned from fetch news job")
                return run_id

            analyzed_news_digest = self.news_analyst.analyze(news_digest)
            news_content = (
                f"Quality: {analyzed_news_digest.quality}\n"
                f"Summary: {analyzed_news_digest.summary or 'N/A'}\n"
                f"Sentiment: {analyzed_news_digest.sentiment or 'N/A'}"
            )
            news_rationale = Rationale(
                run_id=run_id,
                rationale_type=RationaleType.NEWS,
                content=news_content,
                raw_data=None,
            )

            recommendation, synthesis_debug = self.synthesizer.synthesize(
                symbol=symbol,
                timeframe=timeframe,
                technical_view=technical_view,
                news_digest=analyzed_news_digest,
            )

            synthesis_content = (
                f"Action: {recommendation.action}\n"
                f"Brief: {recommendation.brief}\n"
                f"Confidence: {recommendation.confidence:.2%}"
            )
            synthesis_rationale = Rationale(
                run_id=run_id,
                rationale_type=RationaleType.SYNTHESIS,
                content=synthesis_content,
                raw_data=json.dumps(synthesis_debug) if synthesis_debug else None,
            )

            persist_job = PersistRecommendationJob(self.storage, self.artifact_store)
            persist_result = persist_job.run(
                run_id=run_id,
                recommendation=recommendation,
                rationales=[technical_rationale, news_rationale, synthesis_rationale],
            )
            if not persist_result.ok:
                self._mark_run_failed(run_id, persist_result.error)
                return run_id

            self._mark_run_success(run_id)
            return run_id

        except Exception as e:
            self._mark_run_failed(run_id, str(e))
            return run_id

    def _mark_run_failed(self, run_id: int, error_message: str) -> None:
        self.storage.runs.update_run(
            run_id=run_id,
            status=RunStatus.FAILED.value,
            end_time=datetime.now(),
            error_message=error_message,
        )

    def _mark_run_success(self, run_id: int) -> None:
        self.storage.runs.update_run(
            run_id=run_id,
            status=RunStatus.SUCCESS.value,
            end_time=datetime.now(),
            error_message=None,
        )
