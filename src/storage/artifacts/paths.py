from pathlib import Path


class ArtifactPaths:
    def __init__(self, base_dir: Path) -> None:
        self.base_dir = base_dir

    def get_run_dir(self, run_id: int) -> Path:
        return self.base_dir / f"run_{run_id}"

    def ensure_run_dir(self, run_id: int) -> None:
        run_dir = self.get_run_dir(run_id)
        run_dir.mkdir(parents=True, exist_ok=True)
