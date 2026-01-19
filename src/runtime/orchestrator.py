from __future__ import annotations

import json
from datetime import datetime
from time import perf_counter
from typing import TYPE_CHECKING

from src.agents.news_analyst import NewsAnalyst
from src.agents.synthesizer import Synthesizer
from src.agents.technical_analyst import TechnicalAnalyst
from src.agents.verifier import VerifierAgent
from src.core.logging_helpers import stage_timer
from src.core.models.llm import LlmRequest
from src.core.models.rationale import Rationale, RationaleType
from src.core.models.recommendation import Recommendation
from src.core.models.run import Run, RunStatus
from src.core.models.timeframe import Timeframe
from src.core.models.verification import VerificationReport
from src.core.pipeline_trace import PipelineTrace
from src.core.ports.llm_tasks import (
    TASK_NEWS_ANALYSIS,
    TASK_SYNTHESIS,
    TASK_TECH_ANALYSIS,
    TASK_VERIFICATION,
)
from src.core.ports.market_data_provider import MarketDataProvider
from src.core.ports.news_provider import NewsProvider
from src.core.ports.storage import Storage
from src.runtime.config import RuntimeConfig
from src.runtime.jobs.build_features_job import BuildFeaturesJob
from src.runtime.jobs.fetch_market_data_job import FetchMarketDataJob
from src.runtime.jobs.fetch_news_job import FetchNewsJob
from src.runtime.jobs.persist_recommendation_job import PersistRecommendationJob
from src.storage.artifacts.artifact_store import ArtifactStore
from src.storage.sqlite.repositories.candles_repository import CandlesRepository
from src.storage.sqlite.repositories.verification_repository import VerificationRepository
from src.utils.logging import get_logger

if TYPE_CHECKING:
    pass


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
        verifier_enabled: bool | None = None,
        trace: PipelineTrace | None = None,
        config: RuntimeConfig | None = None,
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
        self.verifier_enabled = verifier_enabled
        self.trace = trace or PipelineTrace(enabled=False)
        self.config = config or RuntimeConfig()
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
        self.logger.debug(
            f"Run config: symbol={symbol}, timeframe={timeframe.value}, "
            f"llm_enabled={self.config.llm_enabled}"
        )

        try:
            total_latency_start_time = perf_counter()
            latency_seconds_by_stage: dict[str, float | None] = {}

            provider_name = self.market_data_provider.__class__.__name__.replace(
                "MarketDataProvider", ""
            )
            if not provider_name:
                provider_name = self.market_data_provider.__class__.__name__
            self.trace.step_start(f"Fetching market data from {provider_name}...")
            candles_count = self.config.market_data_window_candles
            stage_start_time = perf_counter()
            with stage_timer(
                "fetch_candles", symbol=symbol, timeframe=timeframe.value, count=candles_count
            ):
                fetch_market_data_job = FetchMarketDataJob(
                    self.market_data_provider, candles_repository=self.candles_repository
                )
                market_result = fetch_market_data_job.run(
                    symbol=symbol,
                    timeframe=timeframe,
                    count=candles_count,
                )
            latency_seconds_by_stage["market_fetch"] = perf_counter() - stage_start_time
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

            self.trace.step_done(f"Loaded {len(candles)} candles")

            self.trace.step_start("Calculating technical indicators...")
            with stage_timer("build_features", symbol=symbol, candles_count=len(candles)):
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
            indicators_count = len(snapshot.indicators) if snapshot.indicators else 0
            self.trace.step_done(f"Calculated {indicators_count} indicators")

            display_symbol = f"{symbol[:3]}/{symbol[3:]}" if len(symbol) == 6 else symbol.upper()
            self.trace.step_start("Running technical analysis (LLM)...")
            stage_start_time = perf_counter()
            with stage_timer("tech_analysis", symbol=symbol, timeframe=timeframe.value):
                technical_view, tech_llm_response = self.technical_analyst.analyze(
                    snapshot, symbol, timeframe
                )
            latency_seconds_by_stage["tech_analysis_llm"] = perf_counter() - stage_start_time
            provider_model = f"{tech_llm_response.provider_name}/{tech_llm_response.model_name}"
            self.trace.step_done(f"Technical analysis complete ({provider_model})")
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

            tech_system_prompt = get_technical_system_prompt(display_symbol, timeframe.value)
            tech_user_prompt = snapshot.to_markdown()

            tech_request = LlmRequest(
                task=TASK_TECH_ANALYSIS,
                system_prompt=tech_system_prompt,
                user_prompt=tech_user_prompt,
                temperature=0.2,
                timeout_seconds=self.config.get_timeout_for_task(TASK_TECH_ANALYSIS),
                max_retries=1,
            )
            self.artifact_store.save_llm_exchange(
                run_id, TASK_TECH_ANALYSIS, tech_request, tech_llm_response
            )

            self.trace.panel(
                f"Technical Rationale ({display_symbol} {timeframe.value})",
                technical_view,
            )

            self.trace.step_start("Fetching news context...")
            stage_start_time = perf_counter()
            with stage_timer("fetch_news", symbol=symbol, timeframe=timeframe.value):
                fetch_news_job = FetchNewsJob(self.news_provider)
                news_result = fetch_news_job.run(symbol=symbol, timeframe=timeframe)
            latency_seconds_by_stage["news_fetch"] = perf_counter() - stage_start_time
            if not news_result.ok:
                self._mark_run_failed(run_id, news_result.error)
                return run_id

            news_digest = news_result.value
            if news_digest is None:
                self._mark_run_failed(run_id, "No news digest returned from fetch news job")
                return run_id

            self.trace.step_done("News context retrieved")

            if news_digest.quality != "LOW":
                self.trace.step_start("Analyzing news with LLM...")
                stage_start_time = perf_counter()
                with stage_timer("news_analysis", symbol=symbol):
                    analyzed_news_digest, news_llm_response = self.news_analyst.analyze(news_digest)
                latency_seconds_by_stage["news_analysis_llm"] = perf_counter() - stage_start_time
                if news_llm_response:
                    provider_model = (
                        f"{news_llm_response.provider_name}/{news_llm_response.model_name}"
                    )
                    self.trace.step_done(f"News analysis complete ({provider_model})")
                else:
                    self.trace.step_done("News analysis complete")
            else:
                analyzed_news_digest = news_digest
                news_llm_response = None
                latency_seconds_by_stage["news_analysis_llm"] = None
            news_content = (
                f"Quality: {analyzed_news_digest.quality}\n"
                f"Summary: {analyzed_news_digest.summary or 'N/A'}\n"
                f"Sentiment: {analyzed_news_digest.sentiment or 'N/A'}"
            )
            news_raw_data: str | None = None
            try:
                news_raw_data = analyzed_news_digest.model_dump_json(
                    exclude={"gdelt_debug"},
                    exclude_none=True,
                )
            except (AttributeError, TypeError, ValueError) as e:
                self.logger.warning(f"Failed to serialize analyzed news digest: {e}")

            news_rationale = Rationale(
                run_id=run_id,
                rationale_type=RationaleType.NEWS,
                content=news_content,
                raw_data=news_raw_data,
                provider_name=news_llm_response.provider_name if news_llm_response else None,
                model_name=news_llm_response.model_name if news_llm_response else None,
                latency_ms=news_llm_response.latency_ms if news_llm_response else None,
                attempts=news_llm_response.attempts if news_llm_response else None,
                error=news_llm_response.error if news_llm_response else None,
            )

            news_panel_lines: list[str] = []
            news_panel_lines.append(
                f"Provider used: {analyzed_news_digest.provider_used or 'NONE'}"
            )
            if analyzed_news_digest.provider_used is None:
                news_panel_lines.append(
                    f"Reason: {analyzed_news_digest.quality_reason or 'News quality too low'}"
                )
            news_panel_lines.append(f"Quality: {analyzed_news_digest.quality}")
            if analyzed_news_digest.summary:
                news_panel_lines.append(f"Summary: {analyzed_news_digest.summary}")
            if analyzed_news_digest.sentiment:
                news_panel_lines.append(f"Sentiment: {analyzed_news_digest.sentiment}")
            if analyzed_news_digest.impact_score is not None:
                news_panel_lines.append(f"Impact Score: {analyzed_news_digest.impact_score:.2f}")
            if analyzed_news_digest.quality_reason:
                news_panel_lines.append(f"Reason: {analyzed_news_digest.quality_reason}")
            if analyzed_news_digest.candidates_total > 0:
                news_panel_lines.append(
                    f"Candidates: {analyzed_news_digest.candidates_total} total, {analyzed_news_digest.articles_after_filter} after filtering"
                )
            if analyzed_news_digest.pass_counts:
                pass_stats: list[str] = []
                for filter_type, counts in analyzed_news_digest.pass_counts.items():
                    pass_stats.append(
                        f"{filter_type}: strict={counts.get('strict', 0)}, medium={counts.get('medium', 0)}, broad={counts.get('broad', 0)}"
                    )
                if pass_stats:
                    news_panel_lines.append("Pass Statistics:")
                    news_panel_lines.extend(f"  {stat}" for stat in pass_stats)
            if analyzed_news_digest.queries_used:
                news_panel_lines.append("Top Queries:")
                for query_tag, query_text in list(analyzed_news_digest.queries_used.items())[:5]:
                    news_panel_lines.append(f"  {query_tag}: {query_text[:80]}...")
            if isinstance(analyzed_news_digest.gdelt_debug, dict):
                passes = analyzed_news_digest.gdelt_debug.get("passes")
                if isinstance(passes, dict):
                    news_panel_lines.append("GDELT Diagnostics (top requests):")
                    request_count = 0
                    for pass_name in ["strict", "medium", "broad"]:
                        pass_data = passes.get(pass_name)
                        if not isinstance(pass_data, dict):
                            continue
                        requests = pass_data.get("requests", [])
                        if not isinstance(requests, list):
                            continue
                        for req in requests[:2]:
                            if request_count >= 3:
                                break
                            if not isinstance(req, dict):
                                continue

                            tag = req.get("tag", "unknown")
                            status = req.get("http_status")
                            items = req.get("items_count", 0)
                            content_type = req.get("content_type")
                            json_parse_error = req.get("json_parse_error")
                            error = req.get("error")

                            status_str = str(status) if status else "?"
                            content_type_text = str(content_type)[:60] if content_type else "None"
                            line = (
                                f"  {tag}: http_status={status_str}, content_type={content_type_text}, "
                                f"items_count={items}"
                            )
                            if error:
                                line += f", error={str(error)[:80]}"
                            if json_parse_error:
                                line += f", json_parse_error={str(json_parse_error)[:120]}"

                            news_panel_lines.append(line)
                            request_count += 1

                        if request_count >= 3:
                            break

            self.trace.panel("News Digest", "\n".join(news_panel_lines))

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
                    timeout_seconds=self.config.get_timeout_for_task(TASK_NEWS_ANALYSIS),
                    max_retries=1,
                )
                self.artifact_store.save_llm_exchange(
                    run_id, TASK_NEWS_ANALYSIS, news_request, news_llm_response
                )

            self.trace.step_start("Synthesizing recommendation (LLM)...")
            stage_start_time = perf_counter()
            with stage_timer("synthesis", symbol=symbol, timeframe=timeframe.value):
                recommendation, synthesis_debug, synthesis_llm_response = (
                    self.synthesizer.synthesize(
                        symbol=symbol,
                        timeframe=timeframe,
                        technical_view=technical_view,
                        news_digest=analyzed_news_digest,
                    )
                )
            latency_seconds_by_stage["synthesis"] = perf_counter() - stage_start_time
            if synthesis_llm_response:
                provider_model = (
                    f"{synthesis_llm_response.provider_name}/{synthesis_llm_response.model_name}"
                )
                self.trace.step_done(f"Recommendation synthesized ({provider_model})")
            else:
                self.trace.step_done("Recommendation synthesized")

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

            synthesis_panel_lines: list[str] = []
            synthesis_panel_lines.append(f"Action: {recommendation.action}")
            synthesis_panel_lines.append(f"Confidence: {recommendation.confidence:.2%}")
            synthesis_panel_lines.append("")
            synthesis_panel_lines.append(recommendation.brief)
            if analyzed_news_digest.quality == "LOW":
                synthesis_panel_lines.append("")
                synthesis_panel_lines.append("System Note: News ignored due to LOW quality")

            self.trace.panel("Synthesis Logic", "\n".join(synthesis_panel_lines))

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
                    timeout_seconds=self.config.get_timeout_for_task(TASK_SYNTHESIS),
                    max_retries=1,
                )
                self.artifact_store.save_llm_exchange(
                    run_id, TASK_SYNTHESIS, synthesis_request, synthesis_llm_response
                )

            verification_report: VerificationReport | None = None
            verifier_enabled_value = self.verifier_enabled
            if verifier_enabled_value is None:
                verifier_enabled_value = self.config.verifier_enabled

            if verifier_enabled_value and self.verifier_agent:
                verification_stage_start_time = perf_counter()
                self.trace.step_start("Verifying recommendation (LLM)...")
                with stage_timer("verification", symbol=symbol):
                    inputs_summary = (
                        f"Technical: {technical_view[:200]}...\nNews: {news_content[:200]}..."
                    )
                    author_output = f"Action: {recommendation.action}\nBrief: {recommendation.brief}\nConfidence: {recommendation.confidence:.2%}"

                    verification_report = self.verifier_agent.verify(
                        task_name=TASK_SYNTHESIS,
                        inputs_summary=inputs_summary,
                        author_output=author_output,
                    )
                if verification_report.provider_name:
                    provider_model = f"{verification_report.provider_name}/{verification_report.model_name or 'N/A'}"
                    self.trace.step_done(f"Verification complete ({provider_model})")
                else:
                    self.trace.step_done("Verification complete")

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
                        timeout_seconds=self.config.get_timeout_for_task(TASK_VERIFICATION),
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

                    if (
                        self.config.verifier_mode == "hard"
                        and verification_report.suggested_fix
                        and self.config.verifier_max_repairs > 0
                    ):
                        repair_count = 0
                        last_recommendation = recommendation
                        last_synthesis_debug = synthesis_debug
                        last_synthesis_llm_response = synthesis_llm_response

                        while repair_count < self.config.verifier_max_repairs:
                            repair_count += 1
                            self.logger.info(
                                f"Run {run_id} attempting repair {repair_count}/{self.config.verifier_max_repairs}"
                            )

                            repair_prompt = f"""Previous synthesis failed verification. Apply the following fix:

VERIFICATION ISSUES:
{json.dumps([{"code": issue.code, "message": issue.message} for issue in verification_report.issues], indent=2)}

SUGGESTED FIX:
{verification_report.suggested_fix}

PREVIOUS OUTPUT:
{last_recommendation.brief}

Generate a corrected synthesis. Do NOT add new facts not in the input data. Return ONLY valid JSON."""

                            repair_llm_response = self.synthesizer.llm_router.generate(
                                task=TASK_SYNTHESIS,
                                system_prompt="Return ONLY valid JSON. No markdown. No explanations. JSON must start with '{' and end with '}'.",
                                user_prompt=repair_prompt,
                            )

                            try:
                                repair_data = json.loads(repair_llm_response.text)
                                repair_recommendation = Recommendation(
                                    symbol=symbol,
                                    timestamp=datetime.now(),
                                    timeframe=timeframe,
                                    action=str(repair_data.get("action", "WAIT")).upper(),
                                    brief=str(repair_data.get("brief", "")),
                                    confidence=float(repair_data.get("confidence", 0.0)),
                                )

                                from src.core.policies.safety_policy import SafetyPolicy

                                safety_policy = SafetyPolicy()
                                validated, _ = safety_policy.validate(repair_recommendation)
                                if validated:
                                    last_recommendation = repair_recommendation
                                    last_synthesis_llm_response = repair_llm_response
                                    self.logger.info(
                                        f"Run {run_id} repair {repair_count} produced valid recommendation"
                                    )

                                    repair_verification = self.verifier_agent.verify(
                                        task_name=TASK_SYNTHESIS,
                                        inputs_summary=inputs_summary,
                                        author_output=f"Action: {repair_recommendation.action}\nBrief: {repair_recommendation.brief}\nConfidence: {repair_recommendation.confidence:.2%}",
                                    )

                                    if repair_verification.passed:
                                        recommendation = repair_recommendation
                                        synthesis_llm_response = repair_llm_response
                                        verification_report = repair_verification
                                        self.logger.info(
                                            f"Run {run_id} repair {repair_count} passed verification"
                                        )
                                        break
                                    else:
                                        verification_report = repair_verification
                                        self.logger.warning(
                                            f"Run {run_id} repair {repair_count} still failed verification"
                                        )
                            except (ValueError, json.JSONDecodeError, KeyError) as e:
                                self.logger.warning(
                                    f"Run {run_id} repair {repair_count} failed to parse: {e}"
                                )

                        if repair_count > 0:
                            synthesis_content = (
                                f"Action: {recommendation.action}\n"
                                f"Brief: {recommendation.brief}\n"
                                f"Confidence: {recommendation.confidence:.2%}"
                            )
                            synthesis_rationale = Rationale(
                                run_id=run_id,
                                rationale_type=RationaleType.SYNTHESIS,
                                content=synthesis_content,
                                raw_data=json.dumps(last_synthesis_debug)
                                if last_synthesis_debug
                                else None,
                                provider_name=last_synthesis_llm_response.provider_name
                                if last_synthesis_llm_response
                                else None,
                                model_name=last_synthesis_llm_response.model_name
                                if last_synthesis_llm_response
                                else None,
                                latency_ms=last_synthesis_llm_response.latency_ms
                                if last_synthesis_llm_response
                                else None,
                                attempts=last_synthesis_llm_response.attempts
                                if last_synthesis_llm_response
                                else None,
                                error=last_synthesis_llm_response.error
                                if last_synthesis_llm_response
                                else None,
                            )

                            if last_synthesis_llm_response:
                                repair_request = LlmRequest(
                                    task=TASK_SYNTHESIS,
                                    system_prompt="Return ONLY valid JSON.",
                                    user_prompt=repair_prompt,
                                    temperature=0.2,
                                    timeout_seconds=self.config.get_timeout_for_task(
                                        TASK_SYNTHESIS
                                    ),
                                    max_retries=1,
                                )
                                self.artifact_store.save_llm_exchange(
                                    run_id,
                                    f"synthesis_repair_{repair_count}",
                                    repair_request,
                                    last_synthesis_llm_response,
                                )

                latency_seconds_by_stage["verification"] = (
                    perf_counter() - verification_stage_start_time
                )
            else:
                latency_seconds_by_stage["verification"] = None

            self.trace.step_start("Saving to database...")
            stage_start_time = perf_counter()
            with stage_timer("persistence", run_id=run_id):
                persist_job = PersistRecommendationJob(self.storage, self.artifact_store)
                persist_result = persist_job.run(
                    run_id=run_id,
                    recommendation=recommendation,
                    rationales=[technical_rationale, news_rationale, synthesis_rationale],
                )
            latency_seconds_by_stage["persistence"] = perf_counter() - stage_start_time
            if not persist_result.ok:
                self._mark_run_failed(run_id, persist_result.error)
                return run_id

            recommendation_id = recommendation.id if recommendation.id else run_id
            self.trace.step_done(f"Saved with ID: {recommendation_id}")

            tech_summary = f"{tech_llm_response.provider_name}/{tech_llm_response.model_name}"
            news_summary = (
                f"{news_llm_response.provider_name}/{news_llm_response.model_name}"
                if news_llm_response
                else "none"
            )
            synthesis_summary = (
                f"{synthesis_llm_response.provider_name}/{synthesis_llm_response.model_name}"
                if synthesis_llm_response
                else "none"
            )
            verify_summary = (
                f"{verification_report.provider_name}/{verification_report.model_name}"
                if verification_report and verification_report.provider_name
                else "none"
            )
            self.trace.llm_summary(tech_summary, news_summary, synthesis_summary, verify_summary)

            if self.trace.enabled:
                total_latency_seconds = perf_counter() - total_latency_start_time
                latency_lines: list[str] = []
                latency_lines.append(f"Total: {total_latency_seconds * 1000:.0f}ms")

                stage_specs: list[tuple[str, str]] = [
                    ("Market fetch", "market_fetch"),
                    ("Tech analysis (LLM)", "tech_analysis_llm"),
                    ("News fetch", "news_fetch"),
                    ("News analysis (LLM)", "news_analysis_llm"),
                    ("Synthesis (LLM)", "synthesis"),
                    ("Verification (LLM)", "verification"),
                    ("Persistence", "persistence"),
                ]
                for label, stage_key in stage_specs:
                    stage_seconds = latency_seconds_by_stage.get(stage_key)
                    if stage_seconds is None:
                        latency_lines.append(f"{label}: skipped")
                    else:
                        latency_lines.append(f"{label}: {stage_seconds * 1000:.0f}ms")

                self.trace.panel("Latency Summary", "\n".join(latency_lines))

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
