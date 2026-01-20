import json

from rich.panel import Panel

from src.core.models.technical_analysis import TechnicalAnalysisResult
from src.utils.json_helpers import extract_json_from_text, try_parse_json


def _truncate_text(value: str, max_length: int) -> str:
    if len(value) <= max_length:
        return value
    return value[:max_length].rstrip() + " ... [truncated]"


def render_technical_view(technical_view: str, *, title: str = "Technical Analysis") -> Panel:
    cleaned = technical_view.strip() if technical_view else ""
    if not cleaned:
        return Panel(
            "[yellow]No technical analysis text was saved.[/yellow]",
            title=title,
            border_style="cyan",
        )

    extracted = extract_json_from_text(cleaned) or cleaned
    parsed = try_parse_json(extracted)

    if parsed is not None:
        try:
            technical = TechnicalAnalysisResult.model_validate(parsed)
            bias = technical.bias
            if bias == "BULLISH":
                bias_display = "[bold green]BULLISH[/bold green]"
                border_style = "green"
            elif bias == "BEARISH":
                bias_display = "[bold red]BEARISH[/bold red]"
                border_style = "red"
            else:
                bias_display = "[bold yellow]NEUTRAL[/bold yellow]"
                border_style = "yellow"

            confidence = float(technical.confidence)
            if confidence >= 0.7:
                confidence_display = f"[green]{confidence:.2%}[/green]"
            elif confidence >= 0.5:
                confidence_display = f"[yellow]{confidence:.2%}[/yellow]"
            else:
                confidence_display = f"[red]{confidence:.2%}[/red]"

            lines: list[str] = []
            lines.append(f"Bias: {bias_display}")
            lines.append(f"Confidence: {confidence_display}")

            if technical.setup_type:
                lines.append(f"Setup: {technical.setup_type}")

            lines.append("")
            lines.append("[bold]Evidence[/bold]")
            if technical.evidence:
                for item in technical.evidence[:12]:
                    lines.append(f"  • {item}")
                if len(technical.evidence) > 12:
                    remaining = len(technical.evidence) - 12
                    lines.append(f"  [dim]... and {remaining} more[/dim]")
            else:
                lines.append("  [dim]None[/dim]")

            lines.append("")
            lines.append("[bold]Contradictions[/bold]")
            if technical.contradictions:
                for item in technical.contradictions[:12]:
                    lines.append(f"  • {item}")
                if len(technical.contradictions) > 12:
                    remaining = len(technical.contradictions) - 12
                    lines.append(f"  [dim]... and {remaining} more[/dim]")
            else:
                lines.append("  [dim]None[/dim]")

            lines.append("")
            lines.append("[bold]Flags[/bold]")
            if technical.no_trade_flags:
                for flag in technical.no_trade_flags[:12]:
                    lines.append(f"  • {flag}")
                if len(technical.no_trade_flags) > 12:
                    remaining = len(technical.no_trade_flags) - 12
                    lines.append(f"  [dim]... and {remaining} more[/dim]")
            else:
                lines.append("  [dim]None[/dim]")

            return Panel("\n".join(lines), title=title, border_style=border_style)
        except ValueError:
            pass

    fallback = cleaned
    try:
        json.loads(extracted)
        fallback = extracted.strip()
    except (TypeError, ValueError, json.JSONDecodeError):
        fallback = cleaned

    fallback = _truncate_text(fallback, 2000)
    return Panel(fallback, title=title, border_style="cyan")
