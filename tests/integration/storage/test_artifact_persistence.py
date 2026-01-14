import json
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock

from src.core.models.rationale import Rationale, RationaleType
from src.core.models.recommendation import Recommendation
from src.core.models.timeframe import Timeframe
from src.core.ports.storage import Storage
from src.runtime.jobs.persist_recommendation_job import PersistRecommendationJob
from src.storage.artifacts.artifact_store import ArtifactStore


def test_artifact_persistence_creates_files() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        artifacts_dir = Path(temp_dir)
        artifact_store = ArtifactStore(artifacts_dir)

        storage = Mock(spec=Storage)
        recommendations_repo = Mock()
        recommendations_repo.save.return_value = 123
        storage.recommendations = recommendations_repo

        rationales_repo = Mock()
        rationales_repo.save.return_value = 456
        storage.rationales = rationales_repo

        job = PersistRecommendationJob(storage=storage, artifact_store=artifact_store)

        recommendation = Recommendation(
            symbol="EURUSD",
            timestamp=datetime.now(),
            timeframe=Timeframe.H1,
            action="CALL",
            brief="Test recommendation",
            confidence=0.75,
        )

        rationales = [
            Rationale(
                run_id=1,
                rationale_type=RationaleType.TECHNICAL,
                content="Technical analysis content",
                raw_data=None,
            ),
            Rationale(
                run_id=1,
                rationale_type=RationaleType.NEWS,
                content="News analysis content",
                raw_data='{"quality": "HIGH"}',
            ),
        ]

        run_id = 1
        result = job.run(run_id=run_id, recommendation=recommendation, rationales=rationales)

        assert result.ok is True

        run_dir = artifacts_dir / f"run_{run_id}"
        assert run_dir.exists()

        recommendation_file = run_dir / "recommendation.json"
        assert recommendation_file.exists()

        with open(recommendation_file, encoding="utf-8") as f:
            recommendation_data = json.load(f)
            assert recommendation_data["symbol"] == "EURUSD"
            assert recommendation_data["action"] == "CALL"
            assert recommendation_data["confidence"] == 0.75
            assert recommendation_data["run_id"] == run_id

        rationales_file = run_dir / "rationales.md"
        assert rationales_file.exists()

        with open(rationales_file, encoding="utf-8") as f:
            rationales_content = f.read()
            assert "## TECHNICAL" in rationales_content
            assert "## NEWS" in rationales_content
            assert "Technical analysis content" in rationales_content
            assert "News analysis content" in rationales_content
