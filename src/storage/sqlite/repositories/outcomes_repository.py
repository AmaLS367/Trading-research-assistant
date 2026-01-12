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
