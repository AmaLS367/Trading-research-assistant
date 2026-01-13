from datetime import datetime

from rich.console import Console
from rich.prompt import Confirm, Prompt

from src.core.models.journal_entry import JournalEntry
from src.core.models.outcome import Outcome
from src.core.ports.storage import Storage

console = Console()


def enter_trade_result(storage: Storage) -> None:
    recommendation = storage.recommendations.get_latest()
    if not recommendation or recommendation.id is None:
        console.print("[red]Error: No recommendation found. Run 'analyze' first.[/red]")
        return

    console.print("[cyan]Latest Recommendation:[/cyan]")
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
        entry_id = storage.journal.save(entry)

        outcome = Outcome(
            journal_entry_id=entry_id,
            close_time=datetime.now(),
            win_or_loss="VOID",
            comment=reason,
        )
        storage.outcomes.save(outcome)

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
    entry_id = storage.journal.save(entry)

    comment = f"Quality: {quality}"
    outcome = Outcome(
        journal_entry_id=entry_id,
        close_time=datetime.now(),
        win_or_loss=result,
        comment=comment,
    )
    storage.outcomes.save(outcome)

    console.print(f"[green]Trade result saved: {result}[/green]")
