import sqlite3
import os
from pathlib import Path
from contextlib import contextmanager
from typing import Generator


class DBConnection:
    def __init__(self, db_path: str = "trading_assistant.db") -> None:
        self.db_path = db_path
        self._ensure_db_directory()

    def _ensure_db_directory(self) -> None:
        db_path_obj = Path(self.db_path)
        db_directory = db_path_obj.parent
        if db_directory != Path(".") and not db_directory.exists():
            db_directory.mkdir(parents=True, exist_ok=True)

    @contextmanager
    def get_cursor(self) -> Generator[sqlite3.Cursor, None, None]:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        cursor = connection.cursor()
        try:
            yield cursor
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def run_migration(self, migration_path: str) -> None:
        if not os.path.exists(migration_path):
            raise FileNotFoundError(f"Migration file not found: {migration_path}")

        with open(migration_path, "r", encoding="utf-8") as migration_file:
            sql = migration_file.read()

        with self.get_cursor() as cursor:
            cursor.executescript(sql)
