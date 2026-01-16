"""Pytest configuration and fixtures."""

import os
import shutil
import subprocess
import sys
from pathlib import Path

# Check for required dependencies
REQUIRED_MODULES = ["tenacity", "ta", "pydantic", "httpx"]


def pytest_configure(config: object) -> None:
    """Configure pytest and check for required dependencies."""
    missing_modules: list[str] = []
    for module in REQUIRED_MODULES:
        try:
            __import__(module)
        except ImportError:
            missing_modules.append(module)

    if missing_modules:
        # tests/conftest.py is in tests/, so project root is one level up
        project_root = Path(__file__).parent.parent
        venv_python = project_root / ".venv" / "Scripts" / "python.exe"
        if not venv_python.exists():
            venv_python = project_root / ".venv" / "bin" / "python"

        # Try to use uv run if available
        if shutil.which("uv"):
            print(
                f"\n⚠️  Missing required modules: {', '.join(missing_modules)}\n"
                f"🔄 Attempting to use 'uv run python -m pytest' instead...\n",
                file=sys.stderr,
            )
            # Re-run with uv run
            cmd = ["uv", "run", "python", "-m", "pytest"] + sys.argv[1:]
            try:
                os.execvp("uv", cmd)
            except OSError:
                # Fallback for Windows
                sys.exit(subprocess.run(cmd).returncode)

        if venv_python.exists():
            print(
                f"\n❌ Missing required modules: {', '.join(missing_modules)}\n"
                f"💡 Please use: uv run python -m pytest\n"
                f"   Or activate virtual environment first.\n"
                f"   Virtual environment Python: {venv_python}\n",
                file=sys.stderr,
            )
        else:
            print(
                f"\n❌ Missing required modules: {', '.join(missing_modules)}\n"
                f"💡 Please run: uv sync --extra dev\n"
                f"   Then use: uv run python -m pytest\n",
                file=sys.stderr,
            )
        sys.exit(1)
