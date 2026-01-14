import tempfile
from datetime import datetime, timedelta
from pathlib import Path

from src.core.models.candle import Candle
from src.core.models.timeframe import Timeframe
from src.storage.sqlite.connection import DBConnection
from src.storage.sqlite.repositories.candles_repository import CandlesRepository


def test_candles_repository_save_and_read() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "test.db"
        db = DBConnection(str(db_path))

        migration_path = Path("src/storage/sqlite/migrations")
        db.run_migration(str(migration_path))

        repo = CandlesRepository(db)

        base_time = datetime(2024, 1, 1, 12, 0, 0)
        test_candles = [
            Candle(
                timestamp=base_time + timedelta(hours=i),
                open=1.0 + i * 0.001,
                high=1.1 + i * 0.001,
                low=0.9 + i * 0.001,
                close=1.05 + i * 0.001,
                volume=1000.0 + i * 10,
            )
            for i in range(10)
        ]

        symbol = "EURUSD"
        timeframe = Timeframe.H1

        repo.upsert_many(symbol=symbol, timeframe=timeframe, candles=test_candles)

        retrieved = repo.get_latest(symbol=symbol, timeframe=timeframe, limit=10)

        assert len(retrieved) == 10
        assert retrieved[0].timestamp == test_candles[0].timestamp
        assert retrieved[0].open == test_candles[0].open
        assert retrieved[9].timestamp == test_candles[9].timestamp
        assert retrieved[9].close == test_candles[9].close

        retrieved_limited = repo.get_latest(symbol=symbol, timeframe=timeframe, limit=5)
        assert len(retrieved_limited) == 5
        assert retrieved_limited[0].timestamp == test_candles[5].timestamp
        assert retrieved_limited[4].timestamp == test_candles[9].timestamp
