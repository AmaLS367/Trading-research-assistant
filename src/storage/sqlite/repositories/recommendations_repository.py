from src.core.models.recommendation import Recommendation
from src.core.models.timeframe import Timeframe
from src.storage.sqlite.connection import DBConnection


class RecommendationsRepository:
    def __init__(self, db: DBConnection) -> None:
        self.db = db

    def save(self, recommendation: Recommendation) -> int:
        query = """
            INSERT INTO recommendations (run_id, symbol, timestamp, timeframe, action, brief, confidence)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        with self.db.get_cursor() as cursor:
            cursor.execute(
                query,
                (
                    recommendation.run_id,
                    recommendation.symbol,
                    recommendation.timestamp.isoformat(),
                    recommendation.timeframe.value,
                    recommendation.action,
                    recommendation.brief,
                    recommendation.confidence,
                ),
            )
            row_id = cursor.lastrowid
            if row_id is None:
                raise RuntimeError("Failed to get lastrowid after insert")
            return row_id

    def get_latest(self) -> Recommendation | None:
        query = "SELECT * FROM recommendations ORDER BY id DESC LIMIT 1"
        with self.db.get_cursor() as cursor:
            cursor.execute(query)
            row = cursor.fetchone()
            if row:
                row_dict = dict(row)
                from datetime import datetime

                row_dict["timestamp"] = datetime.fromisoformat(row_dict["timestamp"])
                row_dict["timeframe"] = Timeframe(row_dict["timeframe"])
                if "action" not in row_dict:
                    row_dict["action"] = "WAIT"
                return Recommendation(**row_dict)
            return None
