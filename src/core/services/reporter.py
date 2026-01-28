import json
from collections import defaultdict
from collections.abc import Sequence

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

            winrate = stats["wins"] / total_trades * 100 if total_trades > 0 else 0.0

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
        table = Table(
            title="News Quality Statistics", show_header=True, header_style="bold magenta"
        )
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
                digest_data: object = json.loads(rationale.raw_data)
                if isinstance(digest_data, str):
                    digest_data = json.loads(digest_data)

                quality_value: object | None = None
                if isinstance(digest_data, dict):
                    quality_value = digest_data.get("quality")

                    if quality_value is None:
                        for nested_key in ["news_digest", "digest", "data"]:
                            nested_value = digest_data.get(nested_key)
                            if isinstance(nested_value, dict):
                                quality_value = nested_value.get("quality")
                                if quality_value is not None:
                                    break

                if quality_value is None:
                    digest = NewsDigest.model_validate(digest_data)
                    quality_value = digest.quality

                quality = str(quality_value).upper()
                if quality in quality_counts:
                    quality_counts[quality] += 1
                    total += 1
            except (json.JSONDecodeError, ValueError, KeyError, TypeError):
                continue

        if total > 0:
            for quality in ["HIGH", "MEDIUM", "LOW"]:
                count = quality_counts[quality]
                percentage = (count / total) * 100
                table.add_row(quality, str(count), f"{percentage:.1f}%")
        else:
            table.add_row("No data", "0", "0.0%")

        return table


def _parse_reason_codes(value: object) -> list[str]:
    if value is None:
        return []

    if isinstance(value, list):
        codes: list[str] = []
        for item in value:
            normalized = str(item).strip().upper()
            if normalized:
                codes.append(normalized)
        return codes

    if not isinstance(value, str):
        return []

    raw = value.strip()
    if not raw:
        return []

    try:
        parsed: object = json.loads(raw)
    except (TypeError, ValueError, json.JSONDecodeError):
        return []

    if isinstance(parsed, str):
        try:
            parsed = json.loads(parsed)
        except (TypeError, ValueError, json.JSONDecodeError):
            return []

    if not isinstance(parsed, list):
        return []

    codes = []
    for item in parsed:
        normalized = str(item).strip().upper()
        if normalized:
            codes.append(normalized)
    return codes


def count_reason_codes(reason_codes_values: Sequence[object]) -> dict[str, int]:
    counts: dict[str, int] = defaultdict(int)
    for value in reason_codes_values:
        for code in _parse_reason_codes(value):
            counts[code] += 1
    return dict(counts)


def generate_reason_codes_table(reason_codes_values: Sequence[object], top_n: int = 10) -> Table:
    counts = count_reason_codes(reason_codes_values)
    total = sum(counts.values())

    table = Table(title="Top Reason Codes", show_header=True, header_style="bold magenta")
    table.add_column("Reason Code", style="cyan", width=32)
    table.add_column("Count", style="yellow", justify="right", width=10)
    table.add_column("Share", style="bold green", justify="right", width=10)

    if total <= 0:
        table.add_row("No data", "0", "0.0%")
        return table

    sorted_items = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    for code, count in sorted_items[: max(1, int(top_n))]:
        share = (count / total) * 100.0
        table.add_row(code, str(count), f"{share:.1f}%")

    return table
