from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from loguru import Logger

    from src.app.settings import Settings


def run_preflight(settings: Settings, logger: Logger, verbose: bool = False) -> None:
    """
    Run preflight checks before analysis:
    1. Check GPU/VRAM availability via check_gpu.py
    2. Download required models via download_models.py based on GPU check results

    This function is safe: any errors are logged but do not stop the analysis pipeline.
    """
    project_root = Path(__file__).parent.parent.parent
    check_gpu_script = project_root / "scripts" / "python" / "check_gpu.py"
    download_models_script = project_root / "scripts" / "python" / "download_models.py"

    if not check_gpu_script.exists():
        logger.info("Preflight: check_gpu.py not found, skipping GPU check")
        return

    if not download_models_script.exists():
        logger.info("Preflight: download_models.py not found, skipping model download")
        return

    try:
        if verbose:
            logger.info("→ Checking GPU/VRAM availability...")

        result = subprocess.run(
            [str(Path(sys.executable)), "-m", "scripts.python.check_gpu"],
            cwd=str(project_root),
            capture_output=True,
            text=True,
            timeout=60,
        )

        if result.returncode != 0:
            logger.warning(f"Preflight: GPU check failed: {result.stderr[:200]}")
            return

        gpu_info = _parse_gpu_check_output(result.stdout)

        if verbose:
            if gpu_info:
                vram_gb = gpu_info.get("min_free_vram_gb", 0)
                logger.info(f"✓ GPU check complete (VRAM: {vram_gb:.1f} GB)")
            else:
                logger.info("✓ GPU check complete (no GPU detected)")

        if download_models_script.exists():
            if verbose:
                logger.info("→ Downloading models from routing configuration...")

            download_result = subprocess.run(
                [
                    str(Path(sys.executable)),
                    "-m",
                    "scripts.python.download_models",
                    "--from-routing",
                ],
                cwd=str(project_root),
                capture_output=True,
                text=True,
                timeout=120,
            )

            if download_result.returncode != 0:
                logger.warning(
                    f"Preflight: Model download failed: {download_result.stderr[:200] or download_result.stdout[:200]}"
                )
            elif verbose:
                logger.info("✓ Model download complete")

    except subprocess.TimeoutExpired:
        logger.warning("Preflight: Script execution timed out, continuing with analysis")
    except FileNotFoundError:
        logger.warning("Preflight: Python executable not found, skipping preflight")
    except Exception as e:
        logger.warning(f"Preflight: Unexpected error: {e}, continuing with analysis")


def _parse_gpu_check_output(output: str) -> dict[str, float] | None:
    """
    Parse GPU check output to extract VRAM information.

    Supports:
    - JSON output (if check_gpu.py is updated to output JSON)
    - Text output with "Minimum free VRAM: X.XX GB" pattern
    - Text output with "Free VRAM: X.XX GB" pattern
    """
    try:
        lines = output.split("\n")
        for line in lines:
            line = line.strip()
            if not line:
                continue

            if line.startswith("{") and line.endswith("}"):
                try:
                    data = json.loads(line)
                    if isinstance(data, dict) and "min_free_vram_gb" in data:
                        return {"min_free_vram_gb": float(data["min_free_vram_gb"])}
                except (json.JSONDecodeError, KeyError, ValueError, TypeError):
                    pass

            vram_match = re.search(
                r"(?:Minimum free VRAM|Free VRAM):\s*([\d.]+)\s*GB", line, re.IGNORECASE
            )
            if vram_match:
                vram_gb = float(vram_match.group(1))
                return {"min_free_vram_gb": vram_gb}

        for line in lines:
            vram_match = re.search(r"vram_gb=([\d.]+)", line, re.IGNORECASE)
            if vram_match:
                vram_gb = float(vram_match.group(1))
                return {"min_free_vram_gb": vram_gb}

    except Exception:
        pass

    return None
