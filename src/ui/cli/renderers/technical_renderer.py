import json

from rich.panel import Panel

from src.core.models.technical_analysis import TechnicalAnalysisResult
from src.utils.json_helpers import extract_json_from_text, try_parse_json

ALLOWED_BIAS_VALUES = {"BULLISH", "BEARISH", "NEUTRAL"}
MAX_LIST_ITEMS = 12
MAX_LIST_ITEM_LEN = 80


def _truncate_text(value: str, max_length: int) -> str:
    if len(value) <= max_length:
        return value
    return value[:max_length].rstrip() + " ... (truncated)"


def _truncate_single_line(text: str, max_len: int) -> str:
    cleaned = " ".join(text.strip().split())
    if len(cleaned) <= max_len:
        return cleaned
    return cleaned[:max_len].rstrip() + " ... (truncated)"


def _safe_string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []

    out: list[str] = []
    for item in value:
        if item is None:
            continue
        out.append(str(item))
    return out


def _build_normalized_technical_candidate(parsed: dict[str, object]) -> dict[str, object] | None:
    bias_raw = parsed.get("bias")
    if not isinstance(bias_raw, str):
        return None

    bias = bias_raw.strip().upper()
    if bias not in ALLOWED_BIAS_VALUES:
        return None

    confidence_raw = parsed.get("confidence")
    confidence: float
    if isinstance(confidence_raw, (int, float)):
        confidence = float(confidence_raw)
    elif isinstance(confidence_raw, str):
        try:
            confidence = float(confidence_raw.strip())
        except ValueError:
            return None
    else:
        return None

    evidence = _safe_string_list(parsed.get("evidence"))
    contradictions = _safe_string_list(parsed.get("contradictions"))
    no_trade_flags = _safe_string_list(parsed.get("no_trade_flags"))

    setup_type_value = parsed.get("setup_type")
    setup_type: str | None = None
    if isinstance(setup_type_value, str) and setup_type_value.strip():
        setup_type = setup_type_value.strip()

    return {
        "bias": bias,
        "confidence": confidence,
        "evidence": evidence,
        "contradictions": contradictions,
        "setup_type": setup_type,
        "no_trade_flags": no_trade_flags,
    }


def _format_bullets(items: list[str], *, max_items: int, max_item_len: int) -> list[str]:
    lines: list[str] = []
    for item in items[:max_items]:
        safe = _truncate_single_line(item, max_item_len)
        lines.append(f"• {safe}")
    if len(items) > max_items:
        remaining = len(items) - max_items
        lines.append(f"[dim]... and {remaining} more[/dim]")
    return lines


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
            normalized = _build_normalized_technical_candidate(parsed)
            if normalized is None:
                technical = TechnicalAnalysisResult.model_validate(parsed)
            else:
                technical = TechnicalAnalysisResult.model_validate(normalized)

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
                safe_setup = _truncate_single_line(str(technical.setup_type), 60)
                lines.append(f"Setup: {safe_setup}")

            lines.append("")
            lines.append("[bold]Evidence[/bold]")
            if technical.evidence:
                lines.extend(
                    _format_bullets(
                        list(technical.evidence),
                        max_items=MAX_LIST_ITEMS,
                        max_item_len=MAX_LIST_ITEM_LEN,
                    )
                )
            else:
                lines.append("  [dim]None[/dim]")

            lines.append("")
            lines.append("[bold]Contradictions[/bold]")
            if technical.contradictions:
                lines.extend(
                    _format_bullets(
                        list(technical.contradictions),
                        max_items=MAX_LIST_ITEMS,
                        max_item_len=MAX_LIST_ITEM_LEN,
                    )
                )
            else:
                lines.append("  [dim]None[/dim]")

            lines.append("")
            lines.append("[bold]Flags[/bold]")
            if technical.no_trade_flags:
                lines.extend(
                    _format_bullets(
                        list(technical.no_trade_flags),
                        max_items=MAX_LIST_ITEMS,
                        max_item_len=MAX_LIST_ITEM_LEN,
                    )
                )
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
