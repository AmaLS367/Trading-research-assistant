import tempfile
from pathlib import Path

from src.app.settings import settings
from src.core.models.rationale import Rationale, RationaleType
from src.storage.sqlite.connection import DBConnection
from src.storage.sqlite.repositories.rationales_repository import RationalesRepository


def test_llm_metadata_persistence():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db = DBConnection(str(db_path))

        db.run_migration(settings.storage_migration_path)

        repository = RationalesRepository(db)

        rationale = Rationale(
            run_id=1,
            rationale_type=RationaleType.TECHNICAL,
            content="Test analysis",
            raw_data='{"test": "data"}',
            provider_name="deepseek_api",
            model_name="deepseek-chat",
            latency_ms=150,
            attempts=1,
            error=None,
        )

        rationale_id = repository.save(rationale)
        assert rationale_id > 0

        retrieved = repository.get_by_run_id(1)
        assert len(retrieved) == 1
        assert retrieved[0].provider_name == "deepseek_api"
        assert retrieved[0].model_name == "deepseek-chat"
        assert retrieved[0].latency_ms == 150
        assert retrieved[0].attempts == 1
        assert retrieved[0].error is None


def test_llm_metadata_with_error():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db = DBConnection(str(db_path))

        db.run_migration(settings.storage_migration_path)

        repository = RationalesRepository(db)

        rationale = Rationale(
            run_id=2,
            rationale_type=RationaleType.SYNTHESIS,
            content="",
            raw_data=None,
            provider_name="ollama_local",
            model_name="llama3:latest",
            latency_ms=50,
            attempts=2,
            error="Network timeout",
        )

        rationale_id = repository.save(rationale)
        assert rationale_id > 0

        retrieved = repository.get_by_run_id(2)
        assert len(retrieved) == 1
        assert retrieved[0].error == "Network timeout"
        assert retrieved[0].attempts == 2
