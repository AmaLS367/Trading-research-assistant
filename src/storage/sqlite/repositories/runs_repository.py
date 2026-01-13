from datetime import datetime
from typing import Optional

from src.core.models.run import Run, RunStatus
from src.core.models.timeframe import Timeframe
from src.storage.sqlite.connection import DBConnection


class RunsRepository:
    def __init__(self, db: DBConnection) -> None:
        self.db = db

    def create(self, run: Run) -> int:
        query = """
            INSERT INTO runs (symbol, timeframe, start_time, end_time, status, error_message)
            VALUES (?, ?, ?, ?, ?, ?)
        """
        with self.db.get_cursor() as cursor:
            cursor.execute(
                query,
                (
                    run.symbol,
                    run.timeframe.value,
                    run.start_time.isoformat(),
                    run.end_time.isoformat() if run.end_time else None,
                    run.status.value,
                    run.error_message,
                ),
            )
            row_id = cursor.lastrowid
            if row_id is None:
                raise RuntimeError("Failed to get lastrowid after inserting run")
            return row_id

    def update_run(
        self,
        run_id: int,
        status: str,
        end_time: datetime,
        error_message: Optional[str],
    ) -> None:
        query = """
            UPDATE runs
            SET status = ?, end_time = ?, error_message = ?
            WHERE id = ?
        """
        with self.db.get_cursor() as cursor:
            cursor.execute(
                query,
                (
                    status,
                    end_time.isoformat(),
                    error_message,
                    run_id,
                ),
            )

    def get_by_id(self, run_id: int) -> Optional[Run]:
        query = """
            SELECT id, symbol, timeframe, start_time, end_time, status, error_message
            FROM runs
            WHERE id = ?
        """
        with self.db.get_cursor() as cursor:
            cursor.execute(query, (run_id,))
            row = cursor.fetchone()
            if not row:
                return None
            row_dict = dict(row)
            row_dict["timeframe"] = Timeframe(row_dict["timeframe"])
            row_dict["start_time"] = datetime.fromisoformat(row_dict["start_time"])
            end_time_raw = row_dict.get("end_time")
            row_dict["end_time"] = (
                datetime.fromisoformat(end_time_raw) if end_time_raw else None
            )
            row_dict["status"] = RunStatus(row_dict["status"])
            return Run(**row_dict)
