import json
from collections import defaultdict

from rich.table import Table

from src.core.models.news import NewsDigest
from src.core.models.rationale import Rationale, RationaleType


class Reporter:
    def __init__(self, outcomes_data: list[dict[str, str | int | None]]) -> None:
        self.outcomes_data = outcomes_data

    def generate_daily_report(self) -> Table:
        table = Table(title="Trading Statistics", show_header=True, header_style="bold magenta")
        table.add_column("Symbol", style="cyan", width=10)
        table.add_column("Total Trades", style="yellow", justify="right", width=12)
        table.add_column("WinRate (%)", style="bold green", justify="right", width=12)
        table.add_column("Wins", style="green", justify="right", width=8)
        table.add_column("Losses", style="red", justify="right", width=8)
        table.add_column("Draws", style="yellow", justify="right", width=8)
        table.add_column("Skipped", style="dim", justify="right", width=8)

        stats_by_symbol: dict[str, dict[str, int]] = defaultdict(
            lambda: {"wins": 0, "losses": 0, "draws": 0, "skipped": 0}
        )

        for outcome in self.outcomes_data:
            symbol_raw = outcome.get("symbol", "UNKNOWN")
            symbol = str(symbol_raw) if symbol_raw is not None else "UNKNOWN"

            result_raw = outcome.get("win_or_loss", "")
            result = str(result_raw).upper() if result_raw is not None else ""

            if result == "WIN":
                stats_by_symbol[symbol]["wins"] += 1
            elif result == "LOSS":
                stats_by_symbol[symbol]["losses"] += 1
            elif result == "DRAW":
                stats_by_symbol[symbol]["draws"] += 1
            elif result == "VOID":
                stats_by_symbol[symbol]["skipped"] += 1

        for symbol in sorted(stats_by_symbol.keys()):
            stats = stats_by_symbol[symbol]
            total_trades = stats["wins"] + stats["losses"] + stats["draws"]
            skipped = stats["skipped"]

            if total_trades > 0:
                winrate = (stats["wins"] / total_trades) * 100
            else:
                winrate = 0.0

            table.add_row(
                symbol,
                str(total_trades),
                f"{winrate:.1f}%",
                str(stats["wins"]),
                str(stats["losses"]),
                str(stats["draws"]),
                str(skipped),
            )

        if not stats_by_symbol:
            table.add_row("No data", "0", "0.0%", "0", "0", "0", "0")

        return table

    def generate_news_stats(self, news_rationales: list[Rationale]) -> Table:
        table = Table(title="News Quality Statistics", show_header=True, header_style="bold magenta")
        table.add_column("Quality", style="cyan", width=10)
        table.add_column("Count", style="yellow", justify="right", width=12)
        table.add_column("Percentage", style="bold green", justify="right", width=12)

        quality_counts: dict[str, int] = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
        total = 0

        for rationale in news_rationales:
            if rationale.rationale_type != RationaleType.NEWS:
                continue
            if not rationale.raw_data:
                continue

            try:
                digest_data = json.loads(rationale.raw_data)
                digest = NewsDigest.model_validate(digest_data)
                quality = digest.quality
                if quality in quality_counts:
                    quality_counts[quality] += 1
                    total += 1
            except (json.JSONDecodeError, ValueError, KeyError):
                continue

        if total > 0:
            for quality in ["HIGH", "MEDIUM", "LOW"]:
                count = quality_counts[quality]
                percentage = (count / total) * 100
                table.add_row(quality, str(count), f"{percentage:.1f}%")
        else:
            table.add_row("No data", "0", "0.0%")

        return table
