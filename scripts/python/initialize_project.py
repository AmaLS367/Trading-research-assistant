"""Initialize project: check environment, install dependencies, setup .env, init DB."""

import subprocess
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from rich.console import Console  # noqa: E402
from rich.panel import Panel  # noqa: E402

console = Console()


def check_python_version() -> bool:
    """Check Python version."""
    version = sys.version_info
    if version.major >= 3 and version.minor >= 11:
        console.print(f"[green]✓[/green] Python {version.major}.{version.minor}.{version.micro}")
        return True
    console.print(
        f"[red]✗[/red] Python {version.major}.{version.minor}.{version.micro} (required: >= 3.11)"
    )
    return False


def install_dependencies() -> bool:
    """Install project dependencies using uv."""
    import shutil

    uv_cmd = shutil.which("uv")
    if not uv_cmd:
        console.print("[red]✗[/red] uv not found. Please install uv first.")
        return False

    console.print("[bold blue]Installing dependencies...[/bold blue]")
    try:
        subprocess.run(
            [uv_cmd, "sync", "--extra", "dev"],
            check=True,
            capture_output=True,
            text=True,
        )
        console.print("[green]✓[/green] Dependencies installed")
        return True
    except subprocess.CalledProcessError as e:
        console.print(f"[red]✗[/red] Failed to install dependencies: {e.stderr}")
        return False
    except Exception as e:
        console.print(f"[red]✗[/red] Error: {e}")
        return False


def setup_env_file() -> bool:
    """Setup .env file if it doesn't exist."""
    env_path = Path(".env")
    if env_path.exists():
        console.print("[yellow]⚠[/yellow] .env file already exists, skipping setup")
        return True

    console.print("[bold blue]Setting up .env file...[/bold blue]")
    try:
        import importlib.util

        project_root = Path(__file__).parent.parent.parent
        setup_path = project_root / "scripts" / "python" / "setup_environment.py"
        spec = importlib.util.spec_from_file_location("setup_environment", setup_path)
        if spec and spec.loader:
            setup_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(setup_module)
            setup_module.setup_interactive()
        return True
    except Exception as e:
        console.print(f"[yellow]⚠[/yellow] Could not setup .env interactively: {e}")
        console.print(
            "[yellow]You can run 'python scripts/python/setup_environment.py' later[/yellow]"
        )
        return True


def init_database() -> bool:
    """Initialize database."""
    console.print("[bold blue]Initializing database...[/bold blue]")
    try:
        import shutil

        python_cmd = shutil.which("python") or sys.executable
        uv_cmd = shutil.which("uv")

        if uv_cmd:
            cmd = [uv_cmd, "run", "python", "-m", "src.app.main", "init-db"]
        else:
            cmd = [python_cmd, "-m", "src.app.main", "init-db"]

        subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True,
        )
        console.print("[green]✓[/green] Database initialized")
        return True
    except subprocess.CalledProcessError as e:
        console.print(f"[red]✗[/red] Failed to initialize database: {e.stderr}")
        return False
    except Exception as e:
        console.print(f"[red]✗[/red] Error: {e}")
        return False


def verify_setup() -> bool:
    """Verify that setup is complete."""
    console.print("[bold blue]Verifying setup...[/bold blue]")

    checks_passed = 0
    total_checks = 3

    env_path = Path(".env")
    if env_path.exists():
        console.print("[green]✓[/green] .env file exists")
        checks_passed += 1
    else:
        console.print("[yellow]⚠[/yellow] .env file not found")

    try:
        from src.app.settings import settings

        db_path = Path(settings.storage_sqlite_db_path)
        if db_path.exists():
            console.print("[green]✓[/green] Database file exists")
            checks_passed += 1
        else:
            console.print("[yellow]⚠[/yellow] Database file not found (run init-db)")

        if settings.oanda_api_key:
            console.print("[green]✓[/green] OANDA API key configured")
            checks_passed += 1
        else:
            console.print("[yellow]⚠[/yellow] OANDA API key not configured")
    except ImportError:
        console.print("[yellow]⚠[/yellow] Cannot import settings")

    return checks_passed == total_checks


def main() -> int:
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Initialize project")
    parser.add_argument(
        "--skip-deps",
        action="store_true",
        help="Skip dependency installation",
    )
    parser.add_argument(
        "--skip-env",
        action="store_true",
        help="Skip .env setup",
    )
    parser.add_argument(
        "--skip-db",
        action="store_true",
        help="Skip database initialization",
    )

    args = parser.parse_args()

    console.print(Panel.fit("[bold blue]Project Initialization[/bold blue]", border_style="blue"))

    if not check_python_version():
        return 1

    if not args.skip_deps:
        if not install_dependencies():
            return 1
    else:
        console.print("[yellow]⚠[/yellow] Skipping dependency installation (--skip-deps)")

    if not args.skip_env:
        setup_env_file()
    else:
        console.print("[yellow]⚠[/yellow] Skipping .env setup (--skip-env)")

    if not args.skip_db:
        if not init_database():
            console.print("[yellow]⚠[/yellow] Database initialization failed, but continuing...")
    else:
        console.print("[yellow]⚠[/yellow] Skipping database initialization (--skip-db)")

    console.print()
    verify_setup()

    console.print()
    console.print(
        Panel.fit("[bold green]Initialization complete![/bold green]", border_style="green")
    )
    console.print("\nNext steps:")
    console.print("  1. Configure your API keys in .env file")
    console.print("  2. Run: python src/app/main.py analyze --symbol EURUSD --timeframe 1h")

    return 0


if __name__ == "__main__":
    sys.exit(main())
