from src.core.models.journal_entry import JournalEntry
from src.storage.sqlite.connection import DBConnection


class JournalRepository:
    def __init__(self, db: DBConnection) -> None:
        self.db = db

    def save(self, entry: JournalEntry) -> int:
        query = """
            INSERT INTO journal_entries (recommendation_id, symbol, open_time, expiry_seconds, user_action)
            VALUES (?, ?, ?, ?, ?)
        """
        with self.db.get_cursor() as cursor:
            cursor.execute(
                query,
                (
                    entry.recommendation_id,
                    entry.symbol,
                    entry.open_time.isoformat(),
                    entry.expiry_seconds,
                    entry.user_action,
                ),
            )
            row_id = cursor.lastrowid
            if row_id is None:
                raise RuntimeError("Failed to get lastrowid after insert")
            return row_id

    def get_latest_by_symbol(self, symbol: str) -> JournalEntry | None:
        query = "SELECT * FROM journal_entries WHERE symbol = ? ORDER BY id DESC LIMIT 1"
        with self.db.get_cursor() as cursor:
            cursor.execute(query, (symbol,))
            row = cursor.fetchone()
            if row:
                row_dict = dict(row)
                from datetime import datetime

                row_dict["open_time"] = datetime.fromisoformat(row_dict["open_time"])
                return JournalEntry(**row_dict)
            return None

    def get_latest(self) -> JournalEntry | None:
        query = "SELECT * FROM journal_entries ORDER BY id DESC LIMIT 1"
        with self.db.get_cursor() as cursor:
            cursor.execute(query)
            row = cursor.fetchone()
            if row:
                row_dict = dict(row)
                from datetime import datetime

                row_dict["open_time"] = datetime.fromisoformat(row_dict["open_time"])
                return JournalEntry(**row_dict)
            return None
