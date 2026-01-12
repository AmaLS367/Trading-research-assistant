from collections import defaultdict

from rich.table import Table


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
