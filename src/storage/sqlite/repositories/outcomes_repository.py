from src.core.models.outcome import Outcome
from src.storage.sqlite.connection import DBConnection


class OutcomesRepository:
    def __init__(self, db: DBConnection) -> None:
        self.db = db

    def save(self, outcome: Outcome) -> int:
        query = """
            INSERT INTO outcomes (journal_entry_id, close_time, win_or_loss, comment)
            VALUES (?, ?, ?, ?)
        """
        with self.db.get_cursor() as cursor:
            cursor.execute(
                query,
                (
                    outcome.journal_entry_id,
                    outcome.close_time.isoformat(),
                    outcome.win_or_loss,
                    outcome.comment,
                ),
            )
            row_id = cursor.lastrowid
            if row_id is None:
                raise RuntimeError("Failed to get lastrowid after insert")
            return row_id

    def get_all_with_details(self) -> list[dict[str, str | int | None]]:
        query = """
            SELECT
                o.id,
                o.journal_entry_id,
                o.close_time,
                o.win_or_loss,
                o.comment,
                j.symbol,
                j.user_action
            FROM outcomes o
            JOIN journal_entries j ON o.journal_entry_id = j.id
            ORDER BY o.close_time DESC
        """
        with self.db.get_cursor() as cursor:
            cursor.execute(query)
            rows = cursor.fetchall()
            result: list[dict[str, str | int | None]] = []
            for row in rows:
                row_dict: dict[str, str | int | None] = dict(row)
                result.append(row_dict)
            return result
