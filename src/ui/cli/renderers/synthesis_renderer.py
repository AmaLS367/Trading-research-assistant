import json
from typing import Any

from rich.panel import Panel

from src.core.models.recommendation import Recommendation
from src.utils.json_helpers import extract_json_from_text, try_parse_json


def _safe_list_of_strings(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    items: list[str] = []
    for item in value:
        if item is None:
            continue
        items.append(str(item))
    return items


def _parse_debug_payload(raw_data: str | None) -> dict[str, Any] | None:
    if not raw_data:
        return None
    try:
        parsed = json.loads(raw_data)
    except (TypeError, ValueError, json.JSONDecodeError):
        return None
    if not isinstance(parsed, dict):
        return None
    return parsed


def _extract_risks_and_reasons(debug_payload: dict[str, Any] | None) -> tuple[list[str], list[str]]:
    if not debug_payload:
        return [], []

    candidate_texts: list[str] = []
    extracted_json = debug_payload.get("extracted_json")
    if isinstance(extracted_json, str) and extracted_json.strip():
        candidate_texts.append(extracted_json)

    raw_output = debug_payload.get("raw_output")
    if isinstance(raw_output, str) and raw_output.strip():
        candidate_texts.append(raw_output)

    for candidate in candidate_texts:
        extracted = extract_json_from_text(candidate) or candidate
        obj = try_parse_json(extracted)
        if isinstance(obj, dict):
            risks = _safe_list_of_strings(obj.get("risks"))
            reasons = _safe_list_of_strings(obj.get("reasons"))
            if risks or reasons:
                return risks, reasons

    return [], []


def render_synthesis(
    recommendation: Recommendation,
    synthesis_raw_data: str | None,
    *,
    title: str = "Synthesis",
) -> Panel:
    action = str(recommendation.action).upper()
    if action == "CALL":
        border_style = "green"
        action_display = "[bold green]CALL[/bold green]"
    elif action == "PUT":
        border_style = "red"
        action_display = "[bold red]PUT[/bold red]"
    else:
        border_style = "yellow"
        action_display = "[bold yellow]WAIT[/bold yellow]"

    confidence_value = float(recommendation.confidence)
    if confidence_value >= 0.7:
        confidence_display = f"[green]{confidence_value:.2%}[/green]"
    elif confidence_value >= 0.5:
        confidence_display = f"[yellow]{confidence_value:.2%}[/yellow]"
    else:
        confidence_display = f"[red]{confidence_value:.2%}[/red]"

    debug_payload = _parse_debug_payload(synthesis_raw_data)

    reason_codes: list[str] = list(recommendation.reason_codes)
    if not reason_codes and debug_payload:
        decision = debug_payload.get("decision")
        if isinstance(decision, dict):
            reason_codes = _safe_list_of_strings(decision.get("reason_codes"))

    risks, reasons = _extract_risks_and_reasons(debug_payload)

    lines: list[str] = []
    lines.append(f"Action: {action_display}")
    lines.append(f"Confidence: {confidence_display}")

    if reason_codes:
        lines.append(f"Reason codes: {', '.join(reason_codes)}")
    else:
        lines.append("Reason codes: [dim]NONE[/dim]")

    lines.append("")
    lines.append("[bold]Brief[/bold]")
    lines.append(recommendation.brief.strip() if recommendation.brief else "")

    if reasons:
        lines.append("")
        lines.append("[bold]Reasons[/bold]")
        for item in reasons[:8]:
            lines.append(f"  • {item}")
        if len(reasons) > 8:
            remaining = len(reasons) - 8
            lines.append(f"  [dim]... and {remaining} more[/dim]")

    lines.append("")
    lines.append("[bold]Risks[/bold]")
    if risks:
        for item in risks[:8]:
            lines.append(f"  • {item}")
        if len(risks) > 8:
            remaining = len(risks) - 8
            lines.append(f"  [dim]... and {remaining} more[/dim]")
    else:
        lines.append("  [dim]None captured[/dim]")

    if debug_payload and debug_payload.get("parse_ok") is False:
        parse_error = debug_payload.get("parse_error")
        if isinstance(parse_error, str) and parse_error.strip():
            lines.append("")
            lines.append(f"[dim]Parse note: {parse_error.strip()}[/dim]")

    return Panel("\n".join(lines), title=title, border_style=border_style)
