import argparse
import json
from datetime import datetime

import httpx
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.table import Table

from src.app.settings import settings
from src.app.wiring import (
    create_minute_loop,
    create_orchestrator,
    create_rationales_repository,
    create_verification_repository,
)
from src.core.models.journal_entry import JournalEntry
from src.core.models.news import NewsDigest
from src.core.models.outcome import Outcome
from src.core.models.rationale import RationaleType
from src.core.models.timeframe import Timeframe
from src.core.pipeline_trace import PipelineTrace
from src.core.services.reporter import Reporter
from src.runtime.preflight import run_preflight
from src.storage.sqlite.connection import DBConnection
from src.storage.sqlite.repositories.journal_repository import JournalRepository
from src.storage.sqlite.repositories.outcomes_repository import OutcomesRepository
from src.storage.sqlite.repositories.recommendations_repository import RecommendationsRepository
from src.utils.logging_setup import setup_logging

console = Console()
db = DBConnection(str(settings.storage_sqlite_db_path))
rec_repo = RecommendationsRepository(db)
journal_repo = JournalRepository(db)
outcome_repo = OutcomesRepository(db)
rationales_repo = create_rationales_repository()
verification_repo = create_verification_repository()


def init_db() -> None:
    db.run_migration(settings.storage_migration_path)
    console.print("[green]Database initialized and migrations applied.[/green]")


def show_latest(show_details: bool = False) -> None:
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

    if show_details:
        if recommendation.run_id is None:
            console.print(
                "[yellow]Details are not available for this recommendation (no run_id). This may be an older entry created before the run tracking system was implemented.[/yellow]"
            )
            return

        rationales = rationales_repo.get_by_run_id(recommendation.run_id)
        if not rationales:
            console.print("[yellow]No rationales found for this run.[/yellow]")
            return

        technical_rationales = [
            r for r in rationales if r.rationale_type == RationaleType.TECHNICAL
        ]
        news_rationales = [r for r in rationales if r.rationale_type == RationaleType.NEWS]
        synthesis_rationales = [
            r for r in rationales if r.rationale_type == RationaleType.SYNTHESIS
        ]

        if technical_rationales:
            tech_rationale = technical_rationales[0]
            content = tech_rationale.content

            metadata_parts: list[str] = []
            if tech_rationale.provider_name:
                metadata_parts.append(f"Provider: {tech_rationale.provider_name}")
            if tech_rationale.model_name:
                metadata_parts.append(f"Model: {tech_rationale.model_name}")
            if tech_rationale.latency_ms is not None:
                metadata_parts.append(f"Latency: {tech_rationale.latency_ms}ms")
            if tech_rationale.attempts is not None:
                metadata_parts.append(f"Attempts: {tech_rationale.attempts}")
            if tech_rationale.error:
                metadata_parts.append(f"[red]Error: {tech_rationale.error}[/red]")

            if metadata_parts:
                content = "\n".join(metadata_parts) + "\n\n" + content

            console.print(Panel(content, title="Technical Analysis", border_style="cyan"))
            console.print()

        if news_rationales:
            news_rationale = news_rationales[0]
            if news_rationale.raw_data:
                try:
                    digest_data = json.loads(news_rationale.raw_data)
                    digest = NewsDigest.model_validate(digest_data)

                    quality_color = (
                        "green"
                        if digest.quality == "HIGH"
                        else "yellow"
                        if digest.quality == "MEDIUM"
                        else "red"
                    )
                    quality_display = f"[{quality_color}]{digest.quality}[/{quality_color}]"

                    digest_parts: list[str] = [f"Quality: {quality_display}"]
                    if digest.provider_used:
                        digest_parts.append(f"Provider used: {digest.provider_used}")
                        if digest.provider_used == "NEWSAPI":
                            reason = digest.primary_reason or digest.quality_reason or ""
                            digest_parts.append(
                                f"Provider selection: GDELT -> fallback to NewsAPI because {reason}"
                                if reason
                                else "Provider selection: GDELT -> fallback to NewsAPI"
                            )
                        elif digest.provider_used == "GDELT":
                            if (
                                digest.quality in ("HIGH", "MEDIUM")
                                and digest.articles_after_filter >= 2
                            ):
                                digest_parts.append("Provider selection: GDELT accepted")
                            else:
                                reason = digest.primary_reason or digest.quality_reason or ""
                                digest_parts.append(
                                    f"Provider selection: GDELT used (fallback unavailable) because {reason}"
                                    if reason
                                    else "Provider selection: GDELT used (fallback unavailable)"
                                )
                        elif digest.provider_used == "NONE":
                            primary_reason = digest.primary_reason or ""
                            secondary_reason = digest.secondary_reason or ""
                            if primary_reason and secondary_reason:
                                digest_parts.append(
                                    f"Provider selection: GDELT -> fallback to NewsAPI; "
                                    f"both rejected (primary: {primary_reason}; secondary: {secondary_reason})"
                                )
                            elif primary_reason:
                                digest_parts.append(
                                    "Provider selection: GDELT -> fallback to NewsAPI; "
                                    f"both rejected (primary: {primary_reason})"
                                )
                            elif secondary_reason:
                                digest_parts.append(
                                    "Provider selection: GDELT -> fallback to NewsAPI; "
                                    f"both rejected (secondary: {secondary_reason})"
                                )
                            else:
                                digest_parts.append(
                                    "Provider selection: GDELT -> fallback to NewsAPI; both rejected"
                                )
                    if digest.summary:
                        digest_parts.append(f"\nSummary: {digest.summary}")
                    if digest.sentiment:
                        sentiment_color = (
                            "green"
                            if digest.sentiment == "POS"
                            else "red"
                            if digest.sentiment == "NEG"
                            else "yellow"
                        )
                        digest_parts.append(
                            f"Sentiment: [{sentiment_color}]{digest.sentiment}[/{sentiment_color}]"
                        )
                    if digest.impact_score is not None:
                        digest_parts.append(f"Impact Score: {digest.impact_score:.2f}")
                    digest_parts.append(f"\nCandidates total: {digest.candidates_total}")
                    digest_parts.append(f"After filtering: {digest.articles_after_filter}")
                    if digest.secondary_quality:
                        digest_parts.append(
                            f"\nSecondary provider: NewsAPI, quality={digest.secondary_quality}, reason={digest.secondary_reason}"
                        )

                    if digest.pass_counts:
                        digest_parts.append("\nPass statistics:")
                        for pass_name in ["strict", "medium", "broad"]:
                            if pass_name in digest.pass_counts:
                                counts = digest.pass_counts[pass_name]
                                digest_parts.append(
                                    f"  {pass_name}: candidates={counts.get('candidates', 0)}, after_filter={counts.get('after_filter', 0)}"
                                )

                    if digest.articles:
                        digest_parts.append("\nTop Articles:")
                        for article in digest.articles[:3]:
                            source_text = f" ({article.source})" if article.source else ""
                            digest_parts.append(f"  • {article.title}{source_text}")
                    if digest.quality == "LOW" and digest.quality_reason:
                        digest_parts.append(f"\nReason: {digest.quality_reason}")
                    if digest.quality == "LOW" and digest.dropped_examples:
                        digest_parts.append("\nDropped examples:")
                        for example in digest.dropped_examples[:3]:
                            digest_parts.append(f"  • {example}")
                    if digest.dropped_reason_hint:
                        digest_parts.append(f"\nDropped reason hint: {digest.dropped_reason_hint}")

                    if (
                        (digest.provider_used == "NONE" or digest.primary_quality)
                        and digest.gdelt_debug
                        and digest.gdelt_debug.get("passes")
                    ):
                        digest_parts.append("\nPrimary (GDELT) diagnostics:")
                        request_count = 0
                        for pass_name in ["strict", "medium", "broad"]:
                            if pass_name in digest.gdelt_debug["passes"]:
                                requests = digest.gdelt_debug["passes"][pass_name].get(
                                    "requests", []
                                )
                                for req in requests[:2]:
                                    if request_count >= 3:
                                        break
                                    tag = req.get("tag", "unknown")
                                    status = req.get("http_status", "?")
                                    items = req.get("items_count", 0)

                                    error = req.get("error")
                                    json_parse_error = req.get("json_parse_error")

                                    content_type = req.get("content_type")
                                    body_length = req.get("body_length")
                                    body_preview = req.get("body_preview")

                                    status_str = str(status) if status else "?"
                                    error_str = f", error: {str(error)[:50]}" if error else ""
                                    digest_parts.append(
                                        f"  {tag}: status={status_str}, items={items}{error_str}"
                                    )

                                    if json_parse_error:
                                        digest_parts.append(
                                            f"    json_parse_error: {str(json_parse_error)[:120]}"
                                        )

                                    if (
                                        content_type is not None
                                        or body_length is not None
                                        or body_preview is not None
                                    ):
                                        content_type_text = (
                                            str(content_type)[:80] if content_type else "None"
                                        )
                                        body_length_text = (
                                            str(body_length) if body_length is not None else "None"
                                        )
                                        body_preview_text = (
                                            str(body_preview)[:200] if body_preview else "None"
                                        )

                                        digest_parts.append(
                                            f"    content_type: {content_type_text}"
                                        )
                                        digest_parts.append(f"    body_length: {body_length_text}")
                                        digest_parts.append(
                                            f"    body_preview: {body_preview_text}"
                                        )

                                    request_count += 1
                                if request_count >= 3:
                                    break

                    digest_content = "\n".join(digest_parts)
                    console.print(
                        Panel(
                            digest_content,
                            title=f"News Digest (Quality: {digest.quality})",
                            border_style="blue",
                        )
                    )
                    console.print()
                except (json.JSONDecodeError, ValueError, KeyError):
                    content = news_rationale.content
                    console.print(Panel(content, title="News Context", border_style="blue"))
                    console.print()
            else:
                content = news_rationale.content
                console.print(Panel(content, title="News Context", border_style="blue"))
                console.print()

        if synthesis_rationales:
            synth_rationale = synthesis_rationales[0]
            content = synth_rationale.content

            synth_metadata_parts: list[str] = []
            if synth_rationale.provider_name:
                synth_metadata_parts.append(f"Provider: {synth_rationale.provider_name}")
            if synth_rationale.model_name:
                synth_metadata_parts.append(f"Model: {synth_rationale.model_name}")
            if synth_rationale.latency_ms is not None:
                synth_metadata_parts.append(f"Latency: {synth_rationale.latency_ms}ms")
            if synth_rationale.attempts is not None:
                synth_metadata_parts.append(f"Attempts: {synth_rationale.attempts}")
            if synth_rationale.error:
                synth_metadata_parts.append(f"[red]Error: {synth_rationale.error}[/red]")

            if synth_metadata_parts:
                content = "\n".join(synth_metadata_parts) + "\n\n" + content

            console.print(Panel(content, title="AI Synthesis", border_style="green"))
            console.print()

        verification_report = verification_repo.get_latest_by_run_id(recommendation.run_id)
        if verification_report:
            verification_parts: list[str] = []
            if verification_report.passed:
                verification_parts.append("[green]✓ Verification PASSED[/green]")
            else:
                verification_parts.append("[red]✗ Verification FAILED[/red]")

            if verification_report.provider_name:
                verification_parts.append(f"Verifier Provider: {verification_report.provider_name}")
            if verification_report.model_name:
                verification_parts.append(f"Verifier Model: {verification_report.model_name}")

            if verification_report.issues:
                verification_parts.append(f"\nIssues ({len(verification_report.issues)}):")
                for issue in verification_report.issues:
                    severity_color = (
                        "red"
                        if issue.severity.value == "high"
                        else "yellow"
                        if issue.severity.value == "medium"
                        else "dim"
                    )
                    verification_parts.append(
                        f"  [{severity_color}]{issue.severity.value.upper()}[/{severity_color}]: {issue.code} - {issue.message}"
                    )
                    if issue.evidence:
                        verification_parts.append(f"    Evidence: {issue.evidence[:100]}...")

            if verification_report.suggested_fix:
                verification_parts.append(f"\nSuggested Fix: {verification_report.suggested_fix}")

            verification_content = "\n".join(verification_parts)
            border_style = "green" if verification_report.passed else "red"
            console.print(
                Panel(
                    verification_content,
                    title="Verification Report",
                    border_style=border_style,
                )
            )
            console.print()


def analyze(symbol: str, timeframe_str: str = "1h", verbose: bool = False) -> None:
    try:
        timeframe = Timeframe(timeframe_str)
    except ValueError:
        console.print(f"[red]Invalid timeframe: {timeframe_str}[/red]")
        console.print("[yellow]Valid timeframes: 1m, 5m, 15m, 1h, 1d[/yellow]")
        return

    from src.utils.market_schedule import is_forex_market_open
    from src.utils.symbol_classifier import classify_symbol_asset_type

    asset_type = classify_symbol_asset_type(symbol)
    if asset_type == "forex":
        if not is_forex_market_open():
            console.print(
                "[yellow]Forex market is closed (weekend). Analysis skipped to avoid stale data and unnecessary LLM usage.[/yellow]"
            )
            return
    elif asset_type == "unknown":
        console.print(
            "[yellow]Warning: Could not classify symbol asset type. Market hours guard skipped.[/yellow]"
        )

    try:
        from loguru import logger

        run_preflight(settings, logger, verbose=verbose)

        if verbose:
            from src.ui.cli.verbose_reporter import RichVerboseReporter

            verbose_reporter = RichVerboseReporter(console)
            trace = PipelineTrace(enabled=True, reporter=verbose_reporter)
            console.print(f"[cyan]Analyzing {symbol} on {timeframe.value} timeframe...[/cyan]")
            console.print()
        else:
            trace = PipelineTrace(enabled=False)
            console.print(f"[cyan]Analyzing {symbol} on {timeframe.value} timeframe...[/cyan]")
            console.print()

        orchestrator = create_orchestrator(trace=trace)
        run_id = orchestrator.run_analysis(symbol=symbol, timeframe=timeframe)

        if not verbose:
            console.print(f"[green]Analysis complete! Run ID: {run_id}[/green]")
            console.print()
            show_latest()
        else:
            console.print()
            console.print(f"[green]Analysis complete! Recommendation ID: {run_id}[/green]")
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

    console.print("[cyan]Latest Recommendation:[/cyan]")
    console.print(f"  Symbol: {recommendation.symbol}")
    console.print(f"  Action: {recommendation.action}")
    console.print(f"  Timeframe: {recommendation.timeframe.value}")
    console.print(f"  Timestamp: {recommendation.timestamp}")
    console.print()

    skip_reason_choices = [
        "Followed WAIT",
        "No setup",
        "Late",
        "Spread",
        "Too risky",
        "Emotion",
        "Other",
    ]

    if recommendation.action == "WAIT":
        selected_action = Prompt.ask(
            "What did you do?",
            choices=["WAIT", "SKIP", "TAKE"],
            default="WAIT",
        )

        if selected_action != "TAKE":
            comment = "WAIT"
            if selected_action == "SKIP":
                comment = Prompt.ask(
                    "Why did you skip?",
                    choices=skip_reason_choices,
                    default="Followed WAIT",
                )
                if comment == "Other":
                    comment = Prompt.ask("Other reason (free text)")

            entry = JournalEntry(
                recommendation_id=recommendation.id,
                symbol=recommendation.symbol,
                open_time=datetime.now(),
                expiry_seconds=300,
                user_action=selected_action,
            )
            entry_id = journal_repo.save(entry)

            outcome = Outcome(
                journal_entry_id=entry_id,
                close_time=datetime.now(),
                win_or_loss="VOID",
                comment=comment,
            )
            outcome_repo.save(outcome)

            console.print(f"[green]Recorded action: {selected_action}[/green]")
            return

        took_trade = True
        user_action = "TAKE"
    else:
        took_trade = Confirm.ask("Did you take this trade?")
        user_action = recommendation.action

    if not took_trade:
        reason = Prompt.ask(
            "Why did you skip?",
            choices=skip_reason_choices,
            default="No setup",
        )
        if reason == "Other":
            reason = Prompt.ask("Other reason (free text)")

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

    quality_choices = [
        "Confident",
        "Calm",
        "Hesitant",
        "Stressed",
        "FOMO",
        "Tired",
        "Other",
    ]
    quality = Prompt.ask(
        "How did you feel about the trade?",
        choices=quality_choices,
        default="Confident",
    )
    if quality == "Other":
        quality = Prompt.ask("Other feeling (free text)")

    confidence: int | None = None
    while True:
        confidence_input = Prompt.ask(
            "Optional confidence 0-100 (press Enter to skip)",
            default="",
            show_default=False,
        ).strip()
        if not confidence_input:
            break

        try:
            parsed_confidence = int(confidence_input)
        except ValueError:
            console.print("[yellow]Please enter a number 0-100, or press Enter to skip.[/yellow]")
            continue

        if parsed_confidence < 0 or parsed_confidence > 100:
            console.print("[yellow]Confidence must be between 0 and 100.[/yellow]")
            continue

        confidence = parsed_confidence
        break

    entry = JournalEntry(
        recommendation_id=recommendation.id,
        symbol=recommendation.symbol,
        open_time=datetime.now(),
        expiry_seconds=300,
        user_action=user_action,
    )
    entry_id = journal_repo.save(entry)

    comment = f"Quality: {quality}"
    if confidence is not None:
        comment = f"{comment}; Confidence: {confidence}"
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

    query = """
        SELECT id, run_id, rationale_type, content, raw_data
        FROM rationales
        WHERE rationale_type = ?
        ORDER BY id ASC
    """
    from src.core.models.rationale import Rationale

    with db.get_cursor() as cursor:
        cursor.execute(query, (RationaleType.NEWS.value,))
        rows = cursor.fetchall()
        news_rationales: list[Rationale] = []
        for row in rows:
            row_dict = dict(row)
            row_dict["rationale_type"] = RationaleType(row_dict["rationale_type"])
            news_rationales.append(Rationale(**row_dict))

    if news_rationales:
        news_table = reporter.generate_news_stats(news_rationales)
        console.print(news_table)
        console.print()


def main() -> None:
    parser = argparse.ArgumentParser(description="Trading Research Assistant CLI")
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("init-db")
    subparsers.add_parser("journal")
    subparsers.add_parser("report")

    show_latest_parser = subparsers.add_parser("show-latest")
    show_latest_parser.add_argument(
        "--details",
        action="store_true",
        help="Show detailed rationale for the latest recommendation",
    )

    analyze_parser = subparsers.add_parser("analyze")
    analyze_parser.add_argument("--symbol", required=True, help="Symbol to analyze (e.g., EURUSD)")
    analyze_parser.add_argument(
        "--timeframe", default="1h", help="Timeframe (1m, 5m, 15m, 1h, 1d). Default: 1h"
    )
    analyze_parser.add_argument(
        "--verbose", action="store_true", help="Show detailed analysis output during execution"
    )

    loop_parser = subparsers.add_parser("loop")
    loop_parser.add_argument("--symbol", required=True, help="Symbol to analyze (e.g., EURUSD)")
    loop_parser.add_argument(
        "--timeframe", default="1h", help="Timeframe (1m, 5m, 15m, 1h, 1d). Default: 1h"
    )
    loop_parser.add_argument(
        "--interval-seconds",
        type=float,
        default=60.0,
        help="Interval between iterations in seconds. Default: 60",
    )
    loop_parser.add_argument(
        "--iterations",
        type=int,
        help="Maximum number of iterations (optional, runs indefinitely if not set)",
    )

    args = parser.parse_args()

    # Configure logging before any operations
    verbose = getattr(args, "verbose", False)
    setup_logging(verbose=verbose)

    if args.command == "init-db":
        init_db()
    elif args.command == "show-latest":
        show_latest(show_details=args.details)
    elif args.command == "analyze":
        analyze(args.symbol, args.timeframe, verbose=args.verbose)
    elif args.command == "loop":
        try:
            timeframe = Timeframe(args.timeframe)
        except ValueError:
            console.print(f"[red]Invalid timeframe: {args.timeframe}[/red]")
            console.print("[yellow]Valid timeframes: 1m, 5m, 15m, 1h, 1d[/yellow]")
            return

        console.print(
            f"[cyan]Starting loop for {args.symbol} on {timeframe.value} timeframe...[/cyan]"
        )
        if args.iterations:
            console.print(f"[dim]Will run {args.iterations} iterations[/dim]")
        console.print()

        loop = create_minute_loop()
        loop.start(
            symbol=args.symbol,
            timeframe=timeframe,
            interval_seconds=args.interval_seconds,
            max_iterations=args.iterations,
        )
    elif args.command == "journal":
        journal()
    elif args.command == "report":
        report()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
