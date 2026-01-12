import argparse
from datetime import datetime

import httpx
from rich.console import Console
from rich.prompt import Confirm, Prompt
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
from src.core.services.reporter import Reporter
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
            console=console,
        )

        console.print(f"[cyan]Analyzing {symbol} on {timeframe.value} timeframe...[/cyan]")
        console.print()
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


def journal() -> None:
    recommendation = rec_repo.get_latest()
    if not recommendation or recommendation.id is None:
        console.print("[red]Error: No recommendation found. Run 'analyze' first.[/red]")
        return

    console.print(f"[cyan]Latest Recommendation:[/cyan]")
    console.print(f"  Symbol: {recommendation.symbol}")
    console.print(f"  Action: {recommendation.action}")
    console.print(f"  Timeframe: {recommendation.timeframe.value}")
    console.print(f"  Timestamp: {recommendation.timestamp}")
    console.print()

    took_trade = Confirm.ask("Did you take this trade?")

    if not took_trade:
        reason = Prompt.ask(
            "Why did you skip?",
            choices=["Market changed", "Too risky", "Missed"],
            default="Market changed",
        )

        entry = JournalEntry(
            recommendation_id=recommendation.id,
            symbol=recommendation.symbol,
            open_time=datetime.now(),
            expiry_seconds=300,
            user_action="SKIP",
        )
        entry_id = journal_repo.save(entry)

        outcome = Outcome(
            journal_entry_id=entry_id,
            close_time=datetime.now(),
            win_or_loss="VOID",
            comment=reason,
        )
        outcome_repo.save(outcome)

        console.print(f"[green]Trade skipped. Reason: {reason}[/green]")
        return

    result = Prompt.ask(
        "What was the result?",
        choices=["WIN", "LOSS", "DRAW"],
        default="WIN",
    )

    quality = Prompt.ask(
        "How did you feel about the trade?",
        choices=["Confident", "Nervous", "Lucky"],
        default="Confident",
    )

    entry = JournalEntry(
        recommendation_id=recommendation.id,
        symbol=recommendation.symbol,
        open_time=datetime.now(),
        expiry_seconds=300,
        user_action=recommendation.action,
    )
    entry_id = journal_repo.save(entry)

    comment = f"Quality: {quality}"
    outcome = Outcome(
        journal_entry_id=entry_id,
        close_time=datetime.now(),
        win_or_loss=result,
        comment=comment,
    )
    outcome_id = outcome_repo.save(outcome)

    console.print(f"[green]Trade logged. Outcome ID: {outcome_id}[/green]")


def report() -> None:
    outcomes_data = outcome_repo.get_all_with_details()
    reporter = Reporter(outcomes_data)
    table = reporter.generate_daily_report()
    console.print(table)
    console.print()


def main() -> None:
    parser = argparse.ArgumentParser(description="Trading Research Assistant CLI")
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("init-db")
    subparsers.add_parser("show-latest")
    subparsers.add_parser("journal")
    subparsers.add_parser("report")

    analyze_parser = subparsers.add_parser("analyze")
    analyze_parser.add_argument("--symbol", required=True, help="Symbol to analyze (e.g., EURUSD)")
    analyze_parser.add_argument(
        "--timeframe", default="1h", help="Timeframe (1m, 5m, 15m, 1h, 1d). Default: 1h"
    )

    args = parser.parse_args()

    if args.command == "init-db":
        init_db()
    elif args.command == "show-latest":
        show_latest()
    elif args.command == "analyze":
        analyze(args.symbol, args.timeframe)
    elif args.command == "journal":
        journal()
    elif args.command == "report":
        report()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
