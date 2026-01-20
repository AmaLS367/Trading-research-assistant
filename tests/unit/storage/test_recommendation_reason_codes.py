from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pytest

from src.core.models.recommendation import Recommendation
from src.core.models.timeframe import Timeframe
from src.storage.sqlite.connection import DBConnection
from src.storage.sqlite.repositories.recommendations_repository import RecommendationsRepository

pytestmark = pytest.mark.unit


def test_recommendations_repo_roundtrips_reason_codes(tmp_path: Path) -> None:
    db_path = tmp_path / "test.sqlite3"
    db = DBConnection(str(db_path))
    db.run_migration("src/storage/sqlite/migrations")

    repo = RecommendationsRepository(db)

    rec = Recommendation(
        run_id=123,
        symbol="EURUSD",
        timestamp=datetime.now(),
        timeframe=Timeframe.H1,
        action="WAIT",
        brief="Test",
        confidence=0.25,
        reason_codes=["LOW_VOLATILITY_NO_SQUEEZE", "NO_FRESH_CROSSOVER"],
    )
    repo.save(rec)

    latest = repo.get_latest()
    assert latest is not None
    assert latest.reason_codes == ["LOW_VOLATILITY_NO_SQUEEZE", "NO_FRESH_CROSSOVER"]
