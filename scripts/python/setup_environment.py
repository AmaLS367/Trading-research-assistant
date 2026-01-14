"""Interactive environment setup helper."""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt

console = Console()

ENV_TEMPLATE = """# --- Application ---
APP_ENV=development
APP_TIMEZONE=Asia/Yerevan

# --- OANDA API (primary provider) ---
OANDA_API_KEY=
OANDA_ACCOUNT_ID=
OANDA_BASE_URL=https://api-fxpractice.oanda.com

# --- Twelve Data API (fallback provider) ---
TWELVE_DATA_API_KEY=
TWELVE_DATA_BASE_URL=https://api.twelvedata.com

# --- GDELT API (news) ---
GDELT_BASE_URL=https://api.gdeltproject.org

# --- NewsAPI (optional) ---
NEWSAPI_API_KEY=
NEWSAPI_BASE_URL=https://newsapi.org

# --- Ollama (LLM) ---
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=

# --- Storage ---
STORAGE_SQLITE_DB_PATH=db/forex_research_assistant.sqlite3
STORAGE_ARTIFACTS_DIR=artifacts
STORAGE_MIGRATION_PATH=src/storage/sqlite/migrations/0001_init.sql

# --- Runtime settings ---
RUNTIME_MVP_SYMBOLS_RAW=EURUSD,GBPUSD,USDJPY
RUNTIME_MVP_TIMEFRAME=1h
RUNTIME_MVP_EXPIRY_SECONDS=300
RUNTIME_LLM_ENABLED=true
RUNTIME_LLM_CALL_INTERVAL_SECONDS=300
RUNTIME_NEWS_REFRESH_INTERVAL_SECONDS=300
RUNTIME_MARKET_DATA_WINDOW_CANDLES=300
"""

REQUIRED_VARS = [
    ("OANDA_API_KEY", "OANDA API key", True),
    ("OANDA_ACCOUNT_ID", "OANDA Account ID", True),
    ("OLLAMA_MODEL", "Ollama model name (e.g., llama3.2)", True),
]

OPTIONAL_VARS = [
    ("TWELVE_DATA_API_KEY", "Twelve Data API key", False),
    ("NEWSAPI_API_KEY", "NewsAPI key", False),
]


def load_existing_env() -> dict[str, str]:
    """Load existing .env file if it exists."""
    env_path = Path(".env")
    if not env_path.exists():
        return {}

    env_vars: dict[str, str] = {}
    with open(env_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, value = line.split("=", 1)
                env_vars[key.strip()] = value.strip()
    return env_vars


def save_env_file(env_vars: dict[str, str]) -> None:
    """Save environment variables to .env file."""
    env_path = Path(".env")
    lines = ENV_TEMPLATE.split("\n")
    result_lines: list[str] = []

    for line in lines:
        if "=" in line and not line.strip().startswith("#"):
            key = line.split("=")[0].strip()
            if key in env_vars:
                result_lines.append(f"{key}={env_vars[key]}")
            else:
                result_lines.append(line)
        else:
            result_lines.append(line)

    with open(env_path, "w", encoding="utf-8") as f:
        f.write("\n".join(result_lines))
    console.print(f"[green]✓[/green] Saved .env file to {env_path.absolute()}")


def create_env_example() -> None:
    """Create .env.example if it doesn't exist."""
    example_path = Path(".env.example")
    if example_path.exists():
        return

    with open(example_path, "w", encoding="utf-8") as f:
        f.write(ENV_TEMPLATE)
    console.print("[green]✓[/green] Created .env.example")


def setup_interactive() -> None:
    """Interactive setup of .env file."""
    console.print(Panel.fit("[bold blue]Environment Setup[/bold blue]", border_style="blue"))

    existing = load_existing_env()
    if existing:
        if not Confirm.ask("Found existing .env file. Overwrite?", default=False):
            console.print("[yellow]Setup cancelled.[/yellow]")
            return

    env_vars: dict[str, str] = existing.copy()

    console.print("\n[bold]Required variables:[/bold]")
    for var_name, description, _ in REQUIRED_VARS:
        current_value = env_vars.get(var_name, "")
        prompt_text = f"{description} [{var_name}]"
        if current_value:
            prompt_text += f" (current: {current_value[:10]}...)"
        value = Prompt.ask(prompt_text, default=current_value)
        if value:
            env_vars[var_name] = value

    console.print("\n[bold]Optional variables (press Enter to skip):[/bold]")
    for var_name, description, _ in OPTIONAL_VARS:
        current_value = env_vars.get(var_name, "")
        prompt_text = f"{description} [{var_name}]"
        if current_value:
            prompt_text += f" (current: {current_value[:10]}...)"
        value = Prompt.ask(prompt_text, default=current_value, show_default=False)
        if value:
            env_vars[var_name] = value

    save_env_file(env_vars)
    create_env_example()

    console.print("\n[green]Setup complete![/green]")


def main() -> int:
    """Main entry point."""
    if len(sys.argv) > 1 and sys.argv[1] == "--non-interactive":
        console.print("[yellow]Non-interactive mode: creating .env.example only[/yellow]")
        create_env_example()
        return 0

    try:
        setup_interactive()
        return 0
    except KeyboardInterrupt:
        console.print("\n[yellow]Setup cancelled by user.[/yellow]")
        return 1
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        return 1


if __name__ == "__main__":
    sys.exit(main())
