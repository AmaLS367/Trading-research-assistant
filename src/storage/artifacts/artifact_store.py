import json
from pathlib import Path
from typing import Any

from src.storage.artifacts.paths import ArtifactPaths


class ArtifactStore:
    def __init__(self, base_dir: Path) -> None:
        self.paths = ArtifactPaths(base_dir)

    def save_json(self, run_id: int, filename: str, data: dict[str, Any]) -> None:
        run_dir = self.paths.get_run_dir(run_id)
        self.paths.ensure_run_dir(run_id)
        file_path = run_dir / filename
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def save_text(self, run_id: int, filename: str, content: str) -> None:
        run_dir = self.paths.get_run_dir(run_id)
        self.paths.ensure_run_dir(run_id)
        file_path = run_dir / filename
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
