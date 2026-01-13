import os
import sqlite3
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
        path = Path(migration_path)

        if path.is_dir():
            sql_files = sorted(p for p in path.glob("*.sql") if p.is_file())
            if not sql_files:
                raise FileNotFoundError(f"No migration files found in directory: {migration_path}")
            self._ensure_schema_migrations_table()
            for sql_file in sql_files:
                if self._is_migration_applied(sql_file.name):
                    continue
                self._apply_migration_file(sql_file)
                self._mark_migration_applied(sql_file.name)
            return

        if not path.exists():
            raise FileNotFoundError(f"Migration file not found: {migration_path}")

        self._apply_migration_file(path)

    def _apply_migration_file(self, file_path: Path) -> None:
        with open(file_path, "r", encoding="utf-8") as migration_file:
            sql = migration_file.read()

        with self.get_cursor() as cursor:
            cursor.executescript(sql)

    def _ensure_schema_migrations_table(self) -> None:
        with self.get_cursor() as cursor:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    filename TEXT PRIMARY KEY,
                    applied_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

    def _is_migration_applied(self, filename: str) -> bool:
        query = "SELECT 1 FROM schema_migrations WHERE filename = ? LIMIT 1"
        with self.get_cursor() as cursor:
            cursor.execute(query, (filename,))
            return cursor.fetchone() is not None

    def _mark_migration_applied(self, filename: str) -> None:
        query = "INSERT INTO schema_migrations (filename) VALUES (?)"
        with self.get_cursor() as cursor:
            cursor.execute(query, (filename,))
