import json

from src.core.models.rationale import Rationale
from src.core.models.recommendation import Recommendation
from src.core.ports.storage import Storage
from src.runtime.jobs.job_result import JobResult
from src.storage.artifacts.artifact_store import ArtifactStore


class PersistRecommendationJob:
    def __init__(self, storage: Storage, artifact_store: ArtifactStore) -> None:
        self.storage = storage
        self.artifact_store = artifact_store

    def run(
        self,
        run_id: int,
        recommendation: Recommendation,
        rationales: list[Rationale],
    ) -> JobResult[None]:
        try:
            recommendation.run_id = run_id
            recommendation_id = self.storage.recommendations.save(recommendation)

            for rationale in rationales:
                rationale.run_id = run_id
                self.storage.rationales.save(rationale)

            recommendation_dict = {
                "id": recommendation_id,
                "run_id": run_id,
                "symbol": recommendation.symbol,
                "timestamp": recommendation.timestamp.isoformat(),
                "timeframe": recommendation.timeframe.value,
                "action": recommendation.action,
                "brief": recommendation.brief,
                "confidence": recommendation.confidence,
            }
            self.artifact_store.save_json(
                run_id=run_id,
                filename="recommendation.json",
                data=recommendation_dict,
            )

            rationales_markdown_parts: list[str] = []
            for rationale in rationales:
                rationales_markdown_parts.append(f"## {rationale.rationale_type.value}")
                rationales_markdown_parts.append("")
                rationales_markdown_parts.append(rationale.content)
                rationales_markdown_parts.append("")
                if rationale.raw_data:
                    rationales_markdown_parts.append("### Raw Data")
                    rationales_markdown_parts.append("")
                    try:
                        raw_data_dict = json.loads(rationale.raw_data)
                        rationales_markdown_parts.append("```json")
                        rationales_markdown_parts.append(json.dumps(raw_data_dict, indent=2))
                        rationales_markdown_parts.append("```")
                    except (json.JSONDecodeError, TypeError):
                        rationales_markdown_parts.append("```")
                        rationales_markdown_parts.append(rationale.raw_data)
                        rationales_markdown_parts.append("```")
                    rationales_markdown_parts.append("")

            rationales_markdown = "\n".join(rationales_markdown_parts)
            self.artifact_store.save_text(
                run_id=run_id,
                filename="rationales.md",
                content=rationales_markdown,
            )

            return JobResult[None](ok=True, value=None, error="")

        except Exception as e:
            return JobResult[None](
                ok=False,
                value=None,
                error=f"Failed to persist recommendation: {str(e)}",
            )
