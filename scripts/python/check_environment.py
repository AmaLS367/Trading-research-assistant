"""Check project environment and dependencies."""
import shutil
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import httpx
from rich.console import Console
from rich.panel import Panel

console = Console()


def check_python_version() -> bool:
    """Check if Python version is >= 3.11."""
    version = sys.version_info
    if version.major >= 3 and version.minor >= 11:
        console.print(f"[green]✓[/green] Python {version.major}.{version.minor}.{version.micro}")
        return True
    console.print(f"[red]✗[/red] Python {version.major}.{version.minor}.{version.micro} (required: >= 3.11)")
    return False


def check_uv() -> bool:
    """Check if uv is available."""
    uv_path = shutil.which("uv")
    if uv_path:
        console.print(f"[green]✓[/green] uv found at {uv_path}")
        return True
    console.print("[yellow]⚠[/yellow] uv not found in PATH (optional but recommended)")
    return True


def check_ollama() -> bool:
    """Check if Ollama server is accessible."""
    try:
        from src.app.settings import settings

        base_url = settings.ollama_base_url
        response = httpx.get(f"{base_url}/api/tags", timeout=5.0)
        if response.status_code == 200:
            console.print(f"[green]✓[/green] Ollama server accessible at {base_url}")
            return True
        console.print(f"[yellow]⚠[/yellow] Ollama server at {base_url} returned status {response.status_code}")
        return False
    except ImportError:
        console.print("[yellow]⚠[/yellow] Cannot import settings (check .env file)")
        return False
    except httpx.RequestError as e:
        console.print(f"[yellow]⚠[/yellow] Ollama server not accessible: {e}")
        return False
    except Exception as e:
        console.print(f"[yellow]⚠[/yellow] Error checking Ollama: {e}")
        return False


def check_env_file() -> bool:
    """Check if .env file exists."""
    env_path = Path(".env")
    if env_path.exists():
        console.print("[green]✓[/green] .env file found")
        return True
    console.print("[red]✗[/red] .env file not found")
    return False


def check_environment_variables() -> tuple[bool, list[str]]:
    """Check required environment variables."""
    try:
        from src.app.settings import settings

        missing: list[str] = []
        required_vars = [
            ("OANDA_API_KEY", settings.oanda_api_key),
            ("OANDA_ACCOUNT_ID", settings.oanda_account_id),
            ("OLLAMA_MODEL", settings.ollama_model),
        ]

        for var_name, value in required_vars:
            if not value or value.strip() == "":
                missing.append(var_name)

        if not missing:
            console.print("[green]✓[/green] Required environment variables are set")
            return True, []
        console.print(f"[yellow]⚠[/yellow] Missing environment variables: {', '.join(missing)}")
        return False, missing
    except ImportError:
        console.print("[yellow]⚠[/yellow] Cannot import settings")
        return False, []
    except Exception as e:
        console.print(f"[yellow]⚠[/yellow] Error checking environment variables: {e}")
        return False, []


def check_database() -> bool:
    """Check if database file exists and is accessible."""
    try:
        from src.app.settings import settings

        db_path = Path(settings.storage_sqlite_db_path)
        if db_path.exists():
            console.print(f"[green]✓[/green] Database file found at {db_path}")
            return True
        console.print(f"[yellow]⚠[/yellow] Database file not found at {db_path} (run init-db to create)")
        return True
    except ImportError:
        console.print("[yellow]⚠[/yellow] Cannot import settings")
        return False
    except Exception as e:
        console.print(f"[yellow]⚠[/yellow] Error checking database: {e}")
        return False


def main() -> int:
    """Run all environment checks."""
    console.print(Panel.fit("[bold blue]Environment Check[/bold blue]", border_style="blue"))

    results: list[bool] = []

    results.append(check_python_version())
    results.append(check_uv())
    results.append(check_env_file())
    env_ok, missing_vars = check_environment_variables()
    results.append(env_ok)
    results.append(check_database())
    results.append(check_ollama())

    console.print()

    all_passed = all(results)
    if all_passed:
        console.print(Panel.fit("[bold green]All checks passed![/bold green]", border_style="green"))
        return 0

    failed_count = sum(1 for r in results if not r)
    console.print(
        Panel.fit(
            f"[bold yellow]{failed_count} check(s) failed or have warnings[/bold yellow]",
            border_style="yellow",
        )
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
