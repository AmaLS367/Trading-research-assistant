import json
from datetime import datetime

from src.agents.news_analyst import NewsAnalyst
from src.agents.synthesizer import Synthesizer
from src.agents.technical_analyst import TechnicalAnalyst
from src.app.settings import settings
from src.core.models.llm import LlmRequest
from src.core.models.rationale import Rationale, RationaleType
from src.core.models.run import Run, RunStatus
from src.core.models.timeframe import Timeframe
from src.core.models.verification import VerificationReport
from src.core.ports.llm_tasks import (
    TASK_NEWS_ANALYSIS,
    TASK_SYNTHESIS,
    TASK_TECH_ANALYSIS,
    TASK_VERIFICATION,
)
from src.core.ports.market_data_provider import MarketDataProvider
from src.core.ports.news_provider import NewsProvider
from src.core.ports.storage import Storage
from src.runtime.jobs.build_features_job import BuildFeaturesJob
from src.runtime.jobs.fetch_market_data_job import FetchMarketDataJob
from src.runtime.jobs.fetch_news_job import FetchNewsJob
from src.runtime.jobs.persist_recommendation_job import PersistRecommendationJob
from src.storage.artifacts.artifact_store import ArtifactStore
from src.storage.sqlite.repositories.candles_repository import CandlesRepository
from src.storage.sqlite.repositories.verification_repository import VerificationRepository
from src.utils.logging import get_logger


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
        candles_repository: CandlesRepository | None = None,
        verifier_agent: VerifierAgent | None = None,
        verification_repository: VerificationRepository | None = None,
    ) -> None:
        self.storage = storage
        self.artifact_store = artifact_store
        self.market_data_provider = market_data_provider
        self.news_provider = news_provider
        self.technical_analyst = technical_analyst
        self.news_analyst = news_analyst
        self.synthesizer = synthesizer
        self.candles_repository = candles_repository
        self.verifier_agent = verifier_agent
        self.verification_repository = verification_repository
        self.logger = get_logger(__name__)

    def run_analysis(self, symbol: str, timeframe: Timeframe) -> int:
        run = Run(
            symbol=symbol,
            timeframe=timeframe,
            start_time=datetime.now(),
            status=RunStatus.PENDING,
        )
        run_id = self.storage.runs.create(run)
        self.logger.info(f"Starting run {run_id} for {symbol} on {timeframe.value}")

        try:
            fetch_market_data_job = FetchMarketDataJob(
                self.market_data_provider, candles_repository=self.candles_repository
            )
            market_result = fetch_market_data_job.run(
                symbol=symbol,
                timeframe=timeframe,
                count=300,
            )
            if not market_result.ok:
                self.logger.error(
                    f"Run {run_id} failed at market data fetch: {market_result.error}"
                )
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

            technical_view, tech_llm_response = self.technical_analyst.analyze(
                snapshot, symbol, timeframe
            )
            technical_rationale = Rationale(
                run_id=run_id,
                rationale_type=RationaleType.TECHNICAL,
                content=technical_view,
                raw_data=None,
                provider_name=tech_llm_response.provider_name,
                model_name=tech_llm_response.model_name,
                latency_ms=tech_llm_response.latency_ms,
                attempts=tech_llm_response.attempts,
                error=tech_llm_response.error,
            )

            from src.agents.prompts.technical_prompts import get_technical_system_prompt

            display_symbol = f"{symbol[:3]}/{symbol[3:]}" if len(symbol) == 6 else symbol.upper()
            tech_system_prompt = get_technical_system_prompt(display_symbol, timeframe.value)
            tech_user_prompt = snapshot.to_markdown()

            tech_request = LlmRequest(
                task=TASK_TECH_ANALYSIS,
                system_prompt=tech_system_prompt,
                user_prompt=tech_user_prompt,
                temperature=0.2,
                timeout_seconds=60.0,
                max_retries=1,
            )
            self.artifact_store.save_llm_exchange(
                run_id, TASK_TECH_ANALYSIS, tech_request, tech_llm_response
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

            analyzed_news_digest, news_llm_response = self.news_analyst.analyze(news_digest)
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
                provider_name=news_llm_response.provider_name if news_llm_response else None,
                model_name=news_llm_response.model_name if news_llm_response else None,
                latency_ms=news_llm_response.latency_ms if news_llm_response else None,
                attempts=news_llm_response.attempts if news_llm_response else None,
                error=news_llm_response.error if news_llm_response else None,
            )

            if news_llm_response:
                from src.agents.prompts.news_prompts import get_news_analysis_system_prompt

                news_system_prompt = get_news_analysis_system_prompt()
                headlines_text = "\n".join(
                    f"- {article.title}" for article in analyzed_news_digest.articles
                )
                news_user_prompt = f"""Analyze the following news headlines for {analyzed_news_digest.symbol}:

{headlines_text}

Provide your analysis as JSON."""

                news_request = LlmRequest(
                    task=TASK_NEWS_ANALYSIS,
                    system_prompt=news_system_prompt,
                    user_prompt=news_user_prompt,
                    temperature=0.2,
                    timeout_seconds=60.0,
                    max_retries=1,
                )
                self.artifact_store.save_llm_exchange(
                    run_id, TASK_NEWS_ANALYSIS, news_request, news_llm_response
                )

            recommendation, synthesis_debug, synthesis_llm_response = self.synthesizer.synthesize(
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
                provider_name=synthesis_llm_response.provider_name
                if synthesis_llm_response
                else None,
                model_name=synthesis_llm_response.model_name if synthesis_llm_response else None,
                latency_ms=synthesis_llm_response.latency_ms if synthesis_llm_response else None,
                attempts=synthesis_llm_response.attempts if synthesis_llm_response else None,
                error=synthesis_llm_response.error if synthesis_llm_response else None,
            )

            if synthesis_llm_response:
                from src.agents.prompts.synthesis_prompts import get_synthesis_system_prompt

                synthesis_system_prompt = get_synthesis_system_prompt()
                news_section_parts: list[str] = []
                if analyzed_news_digest.quality == "LOW":
                    news_section_parts.append(
                        "News Quality: LOW (ignore news, rely on technical analysis)"
                    )
                else:
                    news_section_parts.append(f"News Quality: {analyzed_news_digest.quality}")
                    if analyzed_news_digest.sentiment:
                        news_section_parts.append(
                            f"News Sentiment: {analyzed_news_digest.sentiment}"
                        )
                    if analyzed_news_digest.impact_score is not None:
                        news_section_parts.append(
                            f"News Impact Score: {analyzed_news_digest.impact_score:.2f}"
                        )
                    if analyzed_news_digest.summary:
                        news_section_parts.append(f"News Summary: {analyzed_news_digest.summary}")

                news_section = (
                    "\n".join(news_section_parts) if news_section_parts else "No news available"
                )
                synthesis_user_prompt = f"""Technical Analysis:
{technical_view}

News Context:
{news_section}

Based on the above information, provide your trading recommendation as JSON."""

                synthesis_request = LlmRequest(
                    task=TASK_SYNTHESIS,
                    system_prompt=synthesis_system_prompt,
                    user_prompt=synthesis_user_prompt,
                    temperature=0.2,
                    timeout_seconds=60.0,
                    max_retries=1,
                )
                self.artifact_store.save_llm_exchange(
                    run_id, TASK_SYNTHESIS, synthesis_request, synthesis_llm_response
                )

            verification_report: VerificationReport | None = None
            if settings.llm_verifier_enabled and self.verifier_agent:
                inputs_summary = (
                    f"Technical: {technical_view[:200]}...\nNews: {news_content[:200]}..."
                )
                author_output = f"Action: {recommendation.action}\nBrief: {recommendation.brief}\nConfidence: {recommendation.confidence:.2%}"

                verification_report = self.verifier_agent.verify(
                    task_name=TASK_SYNTHESIS,
                    inputs_summary=inputs_summary,
                    author_output=author_output,
                )

                if self.verification_repository:
                    self.verification_repository.create(run_id, verification_report)

                if verification_report.provider_name and verification_report.model_name:
                    from src.agents.prompts.verifier_prompts import (
                        get_verifier_system_prompt,
                        get_verifier_user_prompt,
                    )

                    verifier_request = LlmRequest(
                        task=TASK_VERIFICATION,
                        system_prompt=get_verifier_system_prompt(),
                        user_prompt=get_verifier_user_prompt(
                            TASK_SYNTHESIS, inputs_summary, author_output
                        ),
                        temperature=0.2,
                        timeout_seconds=60.0,
                        max_retries=1,
                    )
                    from src.core.models.llm import LlmResponse

                    verifier_response = LlmResponse(
                        text=json.dumps(
                            {
                                "passed": verification_report.passed,
                                "issues": [
                                    {
                                        "code": issue.code,
                                        "message": issue.message,
                                        "severity": issue.severity.value,
                                        "evidence": issue.evidence,
                                    }
                                    for issue in verification_report.issues
                                ],
                                "suggested_fix": verification_report.suggested_fix,
                                "policy_version": verification_report.policy_version,
                            }
                        ),
                        provider_name=verification_report.provider_name,
                        model_name=verification_report.model_name,
                        latency_ms=0,
                        attempts=1,
                        error=None,
                    )
                    self.artifact_store.save_llm_exchange(
                        run_id, TASK_VERIFICATION, verifier_request, verifier_response
                    )

                if not verification_report.passed:
                    self.logger.warning(
                        f"Run {run_id} verification failed: {len(verification_report.issues)} issues"
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
            self.logger.info(f"Run {run_id} completed successfully")
            return run_id

        except Exception as e:
            self.logger.exception(f"Run {run_id} failed with exception: {e}")
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
