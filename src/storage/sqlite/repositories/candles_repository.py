from datetime import datetime

from src.core.models.candle import Candle
from src.core.models.timeframe import Timeframe
from src.storage.sqlite.connection import DBConnection


class CandlesRepository:
    def __init__(self, db: DBConnection) -> None:
        self.db = db

    def upsert_many(self, symbol: str, timeframe: Timeframe, candles: list[Candle]) -> None:
        if not candles:
            return

        query = """
            INSERT OR IGNORE INTO candles (symbol, timeframe, timestamp, open, high, low, close, volume)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        with self.db.get_cursor() as cursor:
            for candle in candles:
                cursor.execute(
                    query,
                    (
                        symbol,
                        timeframe.value,
                        candle.timestamp.isoformat(),
                        candle.open,
                        candle.high,
                        candle.low,
                        candle.close,
                        candle.volume,
                    ),
                )

    def get_latest(self, symbol: str, timeframe: Timeframe, limit: int) -> list[Candle]:
        query = """
            SELECT timestamp, open, high, low, close, volume
            FROM candles
            WHERE symbol = ? AND timeframe = ?
            ORDER BY timestamp DESC
            LIMIT ?
        """
        with self.db.get_cursor() as cursor:
            cursor.execute(query, (symbol, timeframe.value, limit))
            rows = cursor.fetchall()

        result: list[Candle] = []
        for row in rows:
            row_dict = dict(row)
            result.append(
                Candle(
                    timestamp=datetime.fromisoformat(row_dict["timestamp"]),
                    open=float(row_dict["open"]),
                    high=float(row_dict["high"]),
                    low=float(row_dict["low"]),
                    close=float(row_dict["close"]),
                    volume=float(row_dict["volume"]),
                )
            )

        result.reverse()
        return result
