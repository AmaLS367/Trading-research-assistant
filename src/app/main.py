import argparse
from datetime import datetime

import httpx
from rich.console import Console
from rich.table import Table

from src.app.settings import settings
from src.app.wiring import (
    create_market_data_provider,
    create_news_provider,
    create_recommendations_repository,
    create_synthesizer,
    create_technical_analyst,
)
from src.core.models.journal_entry import JournalEntry
from src.core.models.outcome import Outcome
from src.core.models.timeframe import Timeframe
from src.runtime.jobs.run_agents_job import RunAgentsJob
from src.storage.sqlite.connection import DBConnection
from src.storage.sqlite.repositories.journal_repository import JournalRepository
from src.storage.sqlite.repositories.outcomes_repository import OutcomesRepository
from src.storage.sqlite.repositories.recommendations_repository import RecommendationsRepository

console = Console()
db = DBConnection(str(settings.storage_sqlite_db_path))
rec_repo = RecommendationsRepository(db)
journal_repo = JournalRepository(db)
outcome_repo = OutcomesRepository(db)


def init_db() -> None:
    db.run_migration(settings.storage_migration_path)
    console.print("[green]Database initialized and migrations applied.[/green]")


def show_latest() -> None:
    recommendation = rec_repo.get_latest()
    if not recommendation:
        console.print("[yellow]No recommendations found.[/yellow]")
        return

    if recommendation.action == "CALL":
        action_color = "green"
    elif recommendation.action == "PUT":
        action_color = "red"
    else:
        action_color = "yellow"
    action_display = f"[{action_color}]{recommendation.action}[/{action_color}]"

    if recommendation.confidence >= 0.7:
        confidence_color = "green"
    elif recommendation.confidence >= 0.5:
        confidence_color = "yellow"
    else:
        confidence_color = "red"
    confidence_display = f"[{confidence_color}]{recommendation.confidence:.2%}[/{confidence_color}]"

    table = Table(title="Latest Recommendation", show_header=True, header_style="bold magenta")
    table.add_column("ID", style="cyan", width=8)
    table.add_column("Symbol", style="magenta", width=10)
    table.add_column("Timeframe", style="green", width=10)
    table.add_column("Action", style="bold", width=8)
    table.add_column("Confidence", style="bold", width=12)
    table.add_column("Brief", width=60)

    table.add_row(
        str(recommendation.id),
        recommendation.symbol,
        recommendation.timeframe.value,
        action_display,
        confidence_display,
        recommendation.brief,
    )
    console.print(table)
    console.print()


def analyze(symbol: str, timeframe_str: str = "1h") -> None:
    try:
        timeframe = Timeframe(timeframe_str)
    except ValueError:
        console.print(f"[red]Invalid timeframe: {timeframe_str}[/red]")
        console.print("[yellow]Valid timeframes: 1m, 5m, 15m, 1h, 1d[/yellow]")
        return

    try:
        market_data_provider = create_market_data_provider()
        news_provider = create_news_provider()
        technical_analyst = create_technical_analyst()
        synthesizer = create_synthesizer()
        recommendations_repo = create_recommendations_repository()

        job = RunAgentsJob(
            market_data_provider=market_data_provider,
            news_provider=news_provider,
            technical_analyst=technical_analyst,
            synthesizer=synthesizer,
            recommendations_repository=recommendations_repo,
        )

        console.print(f"[cyan]Analyzing {symbol} on {timeframe.value} timeframe...[/cyan]")
        recommendation_id = job.run(symbol=symbol, timeframe=timeframe)
        console.print(f"[green]Analysis complete! Recommendation ID: {recommendation_id}[/green]")
        console.print()
        show_latest()
    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
    except httpx.HTTPStatusError as e:
        error_msg = f"HTTP {e.response.status_code}: {e.response.text[:200] if e.response.text else 'Unknown error'}"
        console.print(f"[red]API error: {error_msg}[/red]")
    except Exception as e:
        console.print(f"[red]Unexpected error: {e}[/red]")
        raise


def log_open(symbol: str, action: str, expiry: int) -> None:
    recommendation = rec_repo.get_latest()
    if not recommendation or recommendation.id is None:
        console.print("[red]Error: Cannot log trade without a recommendation.[/red]")
        return

    entry = JournalEntry(
        recommendation_id=recommendation.id,
        symbol=symbol,
        open_time=datetime.now(),
        expiry_seconds=expiry,
        user_action=action,
    )
    entry_id = journal_repo.save(entry)
    console.print(f"[green]Journal entry created with ID: {entry_id}[/green]")


def log_outcome(result: str, comment: str = "") -> None:
    last_journal = journal_repo.get_latest()
    if not last_journal or last_journal.id is None:
        console.print("[red]Error: No open journal entry found to close.[/red]")
        return

    result_upper = result.upper()
    if result_upper not in ["WIN", "LOSS", "DRAW"]:
        console.print("[red]Error: Result must be WIN, LOSS, or DRAW.[/red]")
        return

    outcome = Outcome(
        journal_entry_id=last_journal.id,
        close_time=datetime.now(),
        win_or_loss=result_upper,
        comment=comment,
    )
    outcome_id = outcome_repo.save(outcome)
    console.print(
        f"[green]Outcome logged (ID: {outcome_id}) for Journal ID: {last_journal.id}[/green]"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Trading Research Assistant CLI")
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("init-db")
    subparsers.add_parser("show-latest")

    analyze_parser = subparsers.add_parser("analyze")
    analyze_parser.add_argument("--symbol", required=True, help="Symbol to analyze (e.g., EURUSD)")
    analyze_parser.add_argument(
        "--timeframe", default="1h", help="Timeframe (1m, 5m, 15m, 1h, 1d). Default: 1h"
    )

    open_parser = subparsers.add_parser("log-open")
    open_parser.add_argument("--symbol", required=True)
    open_parser.add_argument("--action", required=True, help="CALL/PUT")
    open_parser.add_argument("--expiry", type=int, default=300, help="Seconds")

    outcome_parser = subparsers.add_parser("log-outcome")
    outcome_parser.add_argument("--result", required=True, help="WIN/LOSS/DRAW")
    outcome_parser.add_argument("--comment", default="")

    args = parser.parse_args()

    if args.command == "init-db":
        init_db()
    elif args.command == "show-latest":
        show_latest()
    elif args.command == "analyze":
        analyze(args.symbol, args.timeframe)
    elif args.command == "log-open":
        log_open(args.symbol, args.action, args.expiry)
    elif args.command == "log-outcome":
        log_outcome(args.result, args.comment)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
