import argparse
from datetime import datetime
from rich.console import Console
from rich.table import Table

from src.app.settings import settings
from src.storage.sqlite.connection import DBConnection
from src.storage.sqlite.repositories.recommendations_repository import RecommendationsRepository
from src.storage.sqlite.repositories.journal_repository import JournalRepository
from src.storage.sqlite.repositories.outcomes_repository import OutcomesRepository
from src.core.models.journal_entry import JournalEntry
from src.core.models.outcome import Outcome

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

    table = Table(title="Latest Recommendation")
    table.add_column("ID", style="cyan")
    table.add_column("Symbol", style="magenta")
    table.add_column("Timeframe", style="green")
    table.add_column("Confidence", style="bold")
    table.add_column("Brief")

    table.add_row(
        str(recommendation.id),
        recommendation.symbol,
        recommendation.timeframe.value,
        f"{recommendation.confidence:.2%}",
        recommendation.brief,
    )
    console.print(table)


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
    elif args.command == "log-open":
        log_open(args.symbol, args.action, args.expiry)
    elif args.command == "log-outcome":
        log_outcome(args.result, args.comment)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
