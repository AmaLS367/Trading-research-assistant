import json
from datetime import datetime

from src.agents.prompts.synthesis_prompts import get_synthesis_system_prompt
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
        news_summary: str,
    ) -> Recommendation:
        system_prompt = get_synthesis_system_prompt()

        user_prompt = f"""Technical Analysis:
{technical_view}

News Context:
{news_summary}

Based on the above information, provide your trading recommendation as JSON."""

        llm_response = self.llm_provider.generate(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
        )

        recommendation_data = self._parse_llm_response(llm_response)

        action_str: str = str(recommendation_data["action"])
        brief_str: str = str(recommendation_data["brief"])
        confidence_float: float = float(recommendation_data["confidence"])

        return Recommendation(
            symbol=symbol,
            timestamp=datetime.now(),
            timeframe=timeframe,
            action=action_str,
            brief=brief_str,
            confidence=confidence_float,
        )

    def _parse_llm_response(self, response: str) -> dict[str, str | float]:
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
            raise ValueError(f"Failed to parse LLM response as JSON: {e}") from e

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

        return {
            "action": action,
            "confidence": confidence,
            "brief": str(data["brief"]),
        }
