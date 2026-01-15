from src.core.models.rationale import Rationale, RationaleType
from src.storage.sqlite.connection import DBConnection


class RationalesRepository:
    def __init__(self, db: DBConnection) -> None:
        self.db = db

    def save(self, rationale: Rationale) -> int:
        query = """
            INSERT INTO rationales (
                run_id, rationale_type, content, raw_data,
                provider_name, model_name, latency_ms, attempts, error
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        with self.db.get_cursor() as cursor:
            cursor.execute(
                query,
                (
                    rationale.run_id,
                    rationale.rationale_type.value,
                    rationale.content,
                    rationale.raw_data,
                    rationale.provider_name,
                    rationale.model_name,
                    rationale.latency_ms,
                    rationale.attempts,
                    rationale.error,
                ),
            )
            row_id = cursor.lastrowid
            if row_id is None:
                raise RuntimeError("Failed to get lastrowid after inserting rationale")
            return row_id

    def get_by_run_id(self, run_id: int) -> list[Rationale]:
        query = """
            SELECT id, run_id, rationale_type, content, raw_data,
                   provider_name, model_name, latency_ms, attempts, error
            FROM rationales
            WHERE run_id = ?
            ORDER BY id ASC
        """
        with self.db.get_cursor() as cursor:
            cursor.execute(query, (run_id,))
            rows = cursor.fetchall()
            rationales: list[Rationale] = []
            if not rows:
                return rationales
            for row in rows:
                row_dict = dict(row)
                row_dict["rationale_type"] = RationaleType(row_dict["rationale_type"])
                rationales.append(Rationale(**row_dict))
            return rationales
