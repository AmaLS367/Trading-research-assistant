import json

from src.agents.prompts.news_prompts import get_news_analysis_system_prompt
from src.core.models.news import NewsDigest
from src.core.ports.llm_provider import LlmProvider


class NewsAnalyst:
    def __init__(self, llm_provider: LlmProvider) -> None:
        self.llm_provider = llm_provider

    def analyze(self, digest: NewsDigest) -> NewsDigest:
        if digest.quality == "LOW":
            digest.summary = "Not enough relevant news"
            digest.sentiment = "NEU"
            digest.impact_score = 0.0
            return digest

        if not digest.articles:
            digest.summary = "Not enough relevant news"
            digest.sentiment = "NEU"
            digest.impact_score = 0.0
            return digest

        system_prompt = get_news_analysis_system_prompt()

        headlines_list: list[str] = []
        for article in digest.articles:
            headline_text = article.title
            if article.source:
                headline_text = f"{headline_text} (Source: {article.source})"
            headlines_list.append(headline_text)

        headlines_text = "\n".join(f"- {headline}" for headline in headlines_list)

        user_prompt = f"""Analyze the following news headlines for {digest.symbol}:

{headlines_text}

Provide your analysis as JSON."""

        try:
            llm_response = self.llm_provider.generate(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
            )

            analysis_data = self._parse_llm_response(
                llm_response, [article.title for article in digest.articles]
            )

            summary_value = analysis_data.get("summary", "Failed to parse LLM output")
            digest.summary = (
                str(summary_value) if summary_value is not None else "Failed to parse LLM output"
            )
            sentiment_value = analysis_data.get("sentiment", "NEU")
            sentiment_str = str(sentiment_value) if sentiment_value is not None else "NEU"
            if sentiment_str not in ["POS", "NEG", "NEU"]:
                sentiment_str = "NEU"
            digest.sentiment = sentiment_str
            impact_score_value = analysis_data.get("impact_score", 0.0)
            impact_score = (
                float(impact_score_value) if isinstance(impact_score_value, (int, float)) else 0.0
            )
            digest.impact_score = max(0.0, min(1.0, impact_score))

        except Exception:
            digest.summary = "Failed to parse LLM output"
            digest.sentiment = "NEU"
            digest.impact_score = 0.0

        return digest

    def _parse_llm_response(
        self, response: str, available_titles: list[str]
    ) -> dict[str, str | float | list[str]]:
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
        except json.JSONDecodeError as err:
            raise ValueError("Failed to parse LLM response as JSON") from err

        if "summary" not in data:
            raise ValueError("LLM response missing 'summary' field")
        if "sentiment" not in data:
            raise ValueError("LLM response missing 'sentiment' field")
        if "impact_score" not in data:
            raise ValueError("LLM response missing 'impact_score' field")

        evidence_titles = data.get("evidence_titles", [])
        if isinstance(evidence_titles, list):
            evidence_titles_filtered = [
                title for title in evidence_titles if title in available_titles
            ]
            data["evidence_titles"] = evidence_titles_filtered
        else:
            data["evidence_titles"] = []

        result: dict[str, str | float | list[str]] = {
            "summary": str(data["summary"]),
            "sentiment": str(data["sentiment"]),
            "impact_score": float(data["impact_score"]),
            "evidence_titles": data["evidence_titles"],
        }
        return result
