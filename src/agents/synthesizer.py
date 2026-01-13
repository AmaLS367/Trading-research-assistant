import json
from datetime import datetime
from typing import Any

from src.agents.prompts.synthesis_prompts import get_synthesis_system_prompt
from src.core.models.news import NewsDigest
from src.core.models.recommendation import Recommendation
from src.core.models.timeframe import Timeframe
from src.core.ports.llm_provider import LlmProvider


class Synthesizer:
    def __init__(self, llm_provider: LlmProvider) -> None:
        self.llm_provider = llm_provider

    def synthesize(
        self,
        symbol: str,
        timeframe: Timeframe,
        technical_view: str,
        news_digest: NewsDigest,
    ) -> tuple[Recommendation, dict[str, Any]]:
        system_prompt = get_synthesis_system_prompt()

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

        user_prompt = f"""Technical Analysis:
{technical_view}

News Context:
{news_section}

Based on the above information, provide your trading recommendation as JSON."""

        llm_response = self.llm_provider.generate(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
        )

        debug_payload: dict[str, Any] = {
            "parse_ok": False,
            "parse_error": None,
            "raw_output": self._truncate_string(llm_response, 6000),
            "retry_used": False,
            "retry_raw_output": None,
            "brief_warning": None,
        }

        try:
            recommendation_data, brief_warning = self._parse_llm_response(llm_response)
            debug_payload["parse_ok"] = True
            debug_payload["brief_warning"] = brief_warning

            action_str: str = str(recommendation_data["action"])
            brief_str: str = str(recommendation_data["brief"])
            confidence_float: float = float(recommendation_data["confidence"])

            recommendation = Recommendation(
                symbol=symbol,
                timestamp=datetime.now(),
                timeframe=timeframe,
                action=action_str,
                brief=brief_str,
                confidence=confidence_float,
            )

            return recommendation, debug_payload

        except (ValueError, json.JSONDecodeError) as parse_error:
            debug_payload["parse_error"] = str(parse_error)

            repair_prompt = f"""Return ONLY valid JSON for the schema. Do not explain. Do not include markdown.

Schema:
{{
    "action": "CALL" or "PUT" or "WAIT",
    "confidence": 0.0 to 1.0,
    "brief": "Brief explanation (single paragraph, no newlines, no curly braces)"
}}

Previous invalid output:
{self._truncate_string(llm_response, 2000)}"""

            try:
                retry_response = self.llm_provider.generate(
                    system_prompt="Return ONLY valid JSON. No markdown. No explanations.",
                    user_prompt=repair_prompt,
                )
                debug_payload["retry_used"] = True
                debug_payload["retry_raw_output"] = self._truncate_string(retry_response, 6000)

                recommendation_data, brief_warning = self._parse_llm_response(retry_response)
                debug_payload["parse_ok"] = True
                debug_payload["brief_warning"] = brief_warning

                action_str: str = str(recommendation_data["action"])
                brief_str: str = str(recommendation_data["brief"])
                confidence_float: float = float(recommendation_data["confidence"])

                recommendation = Recommendation(
                    symbol=symbol,
                    timestamp=datetime.now(),
                    timeframe=timeframe,
                    action=action_str,
                    brief=brief_str,
                    confidence=confidence_float,
                )

                return recommendation, debug_payload

            except (ValueError, json.JSONDecodeError) as retry_error:
                debug_payload["parse_error"] = f"Initial: {parse_error}; Retry: {retry_error}"

                fallback_recommendation = Recommendation(
                    symbol=symbol,
                    timestamp=datetime.now(),
                    timeframe=timeframe,
                    action="WAIT",
                    brief="LLM JSON parse error. News and technical context not synthesized. See rationale for raw output.",
                    confidence=0.0,
                )

                return fallback_recommendation, debug_payload

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

    def _parse_llm_response(self, response: str) -> tuple[dict[str, str | float], str | None]:
        response_cleaned = response.strip()

        if response_cleaned.startswith("```json"):
            response_cleaned = response_cleaned[7:]
        if response_cleaned.startswith("```"):
            response_cleaned = response_cleaned[3:]
        if response_cleaned.endswith("```"):
            response_cleaned = response_cleaned[:-3]
        response_cleaned = response_cleaned.strip()

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
                context_end = min(len(response_cleaned), (error_pos + 150) if error_pos else len(response_cleaned))
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
                fixed = fixed[:json_end + 1]

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
            fixed_quotes = re.sub(
                r'(?<!\\)"(?=.*":\s*")',
                lambda m: '\\"',
                fixed,
                count=1
            )
            json.loads(fixed_quotes)
            return fixed_quotes
        except (json.JSONDecodeError, Exception):
            pass

        return None
