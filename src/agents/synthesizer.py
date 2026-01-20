from __future__ import annotations

import json
from datetime import datetime
from typing import TYPE_CHECKING, Any

from src.agents.prompts.synthesis_prompts import get_synthesis_system_prompt
from src.app.settings import Settings
from src.core.models.news import NewsDigest
from src.core.models.recommendation import Recommendation
from src.core.models.technical_analysis import TechnicalAnalysisResult
from src.core.models.timeframe import Timeframe
from src.core.policies.safety_policy import SafetyPolicy
from src.core.ports.llm_tasks import TASK_SYNTHESIS
from src.decision.policy import decide_action
from src.decision.reason_codes import PARSING_FAILED, build_reason_codes
from src.decision.scoring import calculate_scores
from src.llm.providers.llm_router import LlmRouter
from src.utils.json_helpers import extract_json_from_text, try_parse_json

if TYPE_CHECKING:
    from src.core.models.llm import LlmResponse


class Synthesizer:
    def __init__(self, llm_router: LlmRouter) -> None:
        self.llm_router = llm_router
        self.safety_policy = SafetyPolicy()

    def synthesize(
        self,
        symbol: str,
        timeframe: Timeframe,
        technical_view: str,
        news_digest: NewsDigest,
        indicators: dict[str, object] | None = None,
    ) -> tuple[Recommendation, dict[str, Any], LlmResponse | None]:
        system_prompt = get_synthesis_system_prompt()

        technical, technical_parse_ok, technical_parse_error = self._parse_technical_view(
            technical_view
        )

        scoring_indicators: dict[str, object] = indicators or {}
        technical_scoring_dict: dict[str, object] = {
            "trend_direction": technical.bias,
            "trend_strength": float(technical.confidence) * 100.0,
        }
        scores = calculate_scores(scoring_indicators, technical_analysis=technical_scoring_dict)
        reason_codes = build_reason_codes(scoring_indicators, scores=scores)
        if (not technical_parse_ok or "PARSING_FAILED" in technical.no_trade_flags) and (
            PARSING_FAILED not in reason_codes
        ):
            reason_codes.append(PARSING_FAILED)

        settings = Settings()
        decided_action, decided_confidence = decide_action(
            scores=scores,
            reason_codes=reason_codes,
            settings=settings,
            technical=technical,
        )
        if news_digest.quality == "LOW":
            decided_confidence = min(
                decided_confidence,
                float(settings.decision_max_confidence_when_news_low),
            )

        news_section_parts: list[str] = []
        if news_digest.quality == "LOW":
            news_section_parts.append("News Quality: LOW (ignore news, rely on technical analysis)")
        else:
            news_section_parts.append(f"News Quality: {news_digest.quality}")
            if news_digest.sentiment:
                news_section_parts.append(f"News Sentiment: {news_digest.sentiment}")
            if news_digest.impact_score is not None:
                news_section_parts.append(f"News Impact Score: {news_digest.impact_score:.2f}")
            if news_digest.summary:
                news_section_parts.append(f"News Summary: {news_digest.summary}")
            if news_digest.articles:
                news_section_parts.append("Top News Headlines:")
                for article in news_digest.articles[:5]:
                    news_section_parts.append(f"- {article.title}")

        news_section = "\n".join(news_section_parts) if news_section_parts else "No news available"

        decision_summary = (
            f"Decided Action (fixed): {decided_action}\n"
            f"Decided Confidence (fixed): {decided_confidence:.4f}\n"
            f"Scores: bull={scores.bull_score:.1f}, bear={scores.bear_score:.1f}, "
            f"no_trade={scores.no_trade_score:.1f}\n"
            f"Reason Codes: {', '.join(reason_codes) if reason_codes else 'NONE'}"
        )

        user_prompt = f"""Deterministic Decision (already decided, do NOT change):
{decision_summary}

Technical Analysis (JSON):
{technical.model_dump_json()}

News Context:
{news_section}

Return STRICT JSON ONLY with schema:
{{"action":"CALL|PUT|WAIT","confidence":0.0,"brief":"..."}}

Constraints:
- action MUST be "{decided_action}"
- confidence MUST be {decided_confidence:.4f} (copy exactly)
- brief must explain WHY this decided action makes sense using scores/reason codes/technical/news
"""

        llm_response_obj = self.llm_router.generate(
            task=TASK_SYNTHESIS,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
        )

        debug_payload: dict[str, Any] = {
            "parse_ok": False,
            "parse_error": None,
            "raw_output": self._truncate_string(llm_response_obj.text, 6000),
            "extracted_json": None,
            "repair_attempts": 0,
            "repair_output_1": None,
            "repair_output_2": None,
            "brief_warning": None,
            "retry_used": False,
            "retry_raw_output": None,
            "technical_parse_ok": technical_parse_ok,
            "technical_parse_error": technical_parse_error,
            "decision": {
                "action": decided_action,
                "confidence": decided_confidence,
                "scores": {
                    "bull_score": scores.bull_score,
                    "bear_score": scores.bear_score,
                    "no_trade_score": scores.no_trade_score,
                },
                "reason_codes": reason_codes,
            },
            "llm_metadata": {
                "provider_name": llm_response_obj.provider_name,
                "model_name": llm_response_obj.model_name,
                "latency_ms": llm_response_obj.latency_ms,
                "attempts": llm_response_obj.attempts,
                "error": llm_response_obj.error,
            },
        }

        last_response: LlmResponse | None = llm_response_obj

        try:
            recommendation_data, brief_warning = self._parse_llm_response(llm_response_obj.text)
            extracted_json = self._extract_json(llm_response_obj.text)
            debug_payload["extracted_json"] = self._truncate_string(extracted_json, 2000)
            debug_payload["parse_ok"] = True
            debug_payload["brief_warning"] = brief_warning

            action_str: str = str(recommendation_data["action"])
            brief_str: str = str(recommendation_data["brief"])
            confidence_float: float = float(recommendation_data["confidence"])

            recommendation = Recommendation(
                symbol=symbol,
                timestamp=datetime.now(),
                timeframe=timeframe,
                action=decided_action,
                brief=brief_str,
                confidence=decided_confidence,
            )
            debug_payload["llm_suggested_action"] = action_str
            debug_payload["llm_suggested_confidence"] = confidence_float

            validated, validation_error = self.safety_policy.validate(recommendation)
            if not validated:
                recommendation = self.safety_policy.sanitize(recommendation)
                if validation_error and "forbidden" in validation_error.lower():
                    recommendation.action = "WAIT"
                    recommendation.confidence = min(recommendation.confidence, 0.3)

            return recommendation, debug_payload, last_response

        except (ValueError, json.JSONDecodeError) as parse_error:
            debug_payload["parse_error"] = str(parse_error)
            extracted_json = self._extract_json(llm_response_obj.text)
            debug_payload["extracted_json"] = self._truncate_string(extracted_json, 2000)

            repair_prompt = f"""Convert this into STRICT valid JSON for schema. Return JSON only.

Schema: {{"action":"CALL|PUT|WAIT","confidence":0.0,"brief":"..."}}

Invalid output:
{self._truncate_string(llm_response_obj.text, 1500)}"""

            repair_attempts = 0
            last_error = parse_error

            for attempt in range(2):
                try:
                    repair_attempts += 1
                    debug_payload["repair_attempts"] = repair_attempts
                    debug_payload["retry_used"] = True

                    retry_response_obj = self.llm_router.generate(
                        task=TASK_SYNTHESIS,
                        system_prompt="Return ONLY valid JSON. No markdown. No explanations. JSON must start with '{' and end with '}'.",
                        user_prompt=repair_prompt,
                    )
                    last_response = retry_response_obj

                    if attempt == 0:
                        debug_payload["repair_output_1"] = self._truncate_string(
                            retry_response_obj.text, 6000
                        )
                    else:
                        debug_payload["repair_output_2"] = self._truncate_string(
                            retry_response_obj.text, 6000
                        )

                    recommendation_data, brief_warning = self._parse_llm_response(
                        retry_response_obj.text
                    )
                    debug_payload["parse_ok"] = True
                    debug_payload["brief_warning"] = brief_warning

                    action_str = str(recommendation_data["action"])
                    brief_str = str(recommendation_data["brief"])
                    confidence_float = float(recommendation_data["confidence"])

                    recommendation = Recommendation(
                        symbol=symbol,
                        timestamp=datetime.now(),
                        timeframe=timeframe,
                        action=decided_action,
                        brief=brief_str,
                        confidence=decided_confidence,
                    )
                    debug_payload["llm_suggested_action"] = action_str
                    debug_payload["llm_suggested_confidence"] = confidence_float

                    validated, validation_error = self.safety_policy.validate(recommendation)
                    if not validated:
                        recommendation = self.safety_policy.sanitize(recommendation)
                        if validation_error and "forbidden" in validation_error.lower():
                            recommendation.action = "WAIT"
                            recommendation.confidence = min(recommendation.confidence, 0.3)

                    return recommendation, debug_payload, last_response

                except (ValueError, json.JSONDecodeError) as retry_error:
                    last_error = retry_error
                    debug_payload["retry_raw_output"] = self._truncate_string(
                        retry_response_obj.text, 6000
                    )
                    if attempt == 0:
                        repair_prompt = f"""Convert this into STRICT valid JSON. Return JSON only. JSON must start with '{{' and end with '}}'.

Schema: {{"action":"CALL|PUT|WAIT","confidence":0.0,"brief":"..."}}

Previous failed attempt:
{self._truncate_string(retry_response_obj.text, 1500)}"""

            debug_payload["parse_error"] = f"Initial: {parse_error}; Repair 1: {last_error}"

            fallback_recommendation = Recommendation(
                symbol=symbol,
                timestamp=datetime.now(),
                timeframe=timeframe,
                action=decided_action,
                brief="LLM JSON parse error. Explanation not synthesized. See rationale for raw output.",
                confidence=decided_confidence,
            )

            return fallback_recommendation, debug_payload, last_response

    def _truncate_string(self, text: str, max_length: int) -> str:
        if len(text) <= max_length:
            return text
        return text[:max_length] + "... [truncated]"

    def _normalize_brief(self, brief: str) -> tuple[str, str | None]:
        normalized = brief.strip()

        if normalized.startswith('"') and normalized.endswith('"'):
            normalized = normalized[1:-1]

        if "\n" in normalized:
            normalized = normalized.replace("\n", " ").replace("\r", " ")

        while "  " in normalized:
            normalized = normalized.replace("  ", " ")

        warning: str | None = None
        if "{" in normalized or "}" in normalized:
            warning = "Brief contains curly braces (possible nested JSON)"

        return normalized, warning

    def _extract_json(self, text: str) -> str:
        text = text.strip()

        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()

        json_start = text.find("{")
        if json_start < 0:
            return text

        json_end = text.rfind("}")
        if json_end < json_start:
            json_end = len(text) - 1

        extracted = text[json_start : json_end + 1]

        if not extracted.endswith("}"):
            extracted = extracted + "}"

        extracted = extracted.replace('"', '"').replace('"', '"')
        extracted = extracted.replace(""", "'").replace(""", "'")

        return extracted

    def _parse_llm_response(self, response: str) -> tuple[dict[str, str | float], str | None]:
        response_cleaned = self._extract_json(response)

        try:
            data = json.loads(response_cleaned)
        except json.JSONDecodeError as e:
            try:
                fixed_response = self._try_fix_json(response_cleaned)
                if fixed_response:
                    data = json.loads(fixed_response)
                else:
                    raise
            except (json.JSONDecodeError, ValueError):
                error_pos = getattr(e, "pos", None)
                error_line = getattr(e, "lineno", None)
                error_col = getattr(e, "colno", None)

                context_start = max(0, (error_pos - 150) if error_pos else 0)
                context_end = min(
                    len(response_cleaned), (error_pos + 150) if error_pos else len(response_cleaned)
                )
                context = response_cleaned[context_start:context_end]

                error_details = f" at position {error_pos}" if error_pos else ""
                if error_line and error_col:
                    error_details += f" (line {error_line}, column {error_col})"

                error_msg = f"Failed to parse LLM response as JSON{error_details}: {e}"
                if context:
                    error_msg += f"\nContext around error:\n{context}"
                if len(response_cleaned) > 0:
                    error_msg += f"\nFull response length: {len(response_cleaned)} chars"
                    error_msg += f"\nFirst 200 chars: {response_cleaned[:200]}"
                    if len(response_cleaned) > 200:
                        error_msg += f"\nLast 200 chars: {response_cleaned[-200:]}"

                raise ValueError(error_msg) from e

        if "action" not in data:
            raise ValueError("LLM response missing 'action' field")
        if "confidence" not in data:
            raise ValueError("LLM response missing 'confidence' field")
        if "brief" not in data:
            raise ValueError("LLM response missing 'brief' field")

        action = str(data["action"]).upper()
        if action not in ["CALL", "PUT", "WAIT"]:
            raise ValueError(f"Invalid action: {action}. Must be CALL, PUT, or WAIT")

        confidence = float(data["confidence"])
        if not 0.0 <= confidence <= 1.0:
            raise ValueError(f"Confidence must be between 0.0 and 1.0, got {confidence}")

        brief_raw = str(data["brief"])
        brief_normalized, brief_warning = self._normalize_brief(brief_raw)

        return {
            "action": action,
            "confidence": confidence,
            "brief": brief_normalized,
        }, brief_warning

    def _try_fix_json(self, json_str: str) -> str | None:
        fixed = json_str

        if not fixed.strip().startswith("{"):
            json_start = fixed.find("{")
            if json_start >= 0:
                fixed = fixed[json_start:]

        if not fixed.strip().endswith("}"):
            json_end = fixed.rfind("}")
            if json_end >= 0:
                fixed = fixed[: json_end + 1]

        try:
            json.loads(fixed)
            return fixed
        except json.JSONDecodeError:
            pass

        import re

        try:
            fixed_escapes = fixed.replace("\\'", "'")
            json.loads(fixed_escapes)
            return fixed_escapes
        except (json.JSONDecodeError, Exception):
            pass

        try:
            fixed_quotes = re.sub(r'(?<!\\)"(?=.*":\s*")', lambda m: '\\"', fixed, count=1)
            json.loads(fixed_quotes)
            return fixed_quotes
        except (json.JSONDecodeError, Exception):
            pass

        return None

    def _parse_technical_view(
        self, technical_view: str
    ) -> tuple[TechnicalAnalysisResult, bool, str | None]:
        extracted = extract_json_from_text(technical_view) or technical_view
        parsed = try_parse_json(extracted)

        if parsed is not None:
            try:
                technical = TechnicalAnalysisResult.model_validate(parsed)
                return technical, True, None
            except ValueError as e:
                return self._fallback_technical_result(parse_error=str(e)), False, str(e)

        return (
            self._fallback_technical_result(parse_error="technical_view is not valid JSON"),
            False,
            ("technical_view is not valid JSON"),
        )

    def _fallback_technical_result(self, parse_error: str) -> TechnicalAnalysisResult:
        _ = parse_error
        return TechnicalAnalysisResult(
            bias="NEUTRAL",
            confidence=0.0,
            evidence=[],
            contradictions=[],
            setup_type=None,
            no_trade_flags=["PARSING_FAILED"],
        )
