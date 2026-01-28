import os

from rich.console import Console
from rich.panel import Panel


def _is_news_debug_enabled() -> bool:
    value = os.getenv("TRA_NEWS_DEBUG", "").strip().lower()
    return value in {"1", "true", "yes", "y", "on"}


def _truncate_single_line(text: str, max_len: int) -> str:
    cleaned = " ".join(text.strip().split())
    if len(cleaned) <= max_len:
        return cleaned
    return cleaned[:max_len].rstrip() + " ... [truncated]"


def _compact_news_digest_body(body: str) -> str:
    lines = [line.rstrip() for line in (body or "").splitlines()]

    provider_used: str | None = None
    quality: str | None = None
    summary: str | None = None
    quality_reason: str | None = None
    headlines: list[str] = []

    def _matches_prefix(line: str, prefix: str) -> bool:
        return line.strip().lower().startswith(prefix.lower())

    def _value_after_colon(line: str) -> str:
        parts = line.split(":", 1)
        if len(parts) == 2:
            return parts[1].strip()
        return line.strip()

    headline_section_active = False
    for raw in lines:
        line = raw.strip()
        if not line:
            continue

        if _matches_prefix(line, "provider used:"):
            provider_used = _value_after_colon(line)
            continue
        if _matches_prefix(line, "quality:"):
            quality = _value_after_colon(line)
            continue
        if _matches_prefix(line, "summary:"):
            summary = _value_after_colon(line)
            continue
        if _matches_prefix(line, "reason:") or _matches_prefix(line, "quality reason:"):
            quality_reason = _value_after_colon(line)
            continue

        lower = line.lower()
        if lower in {"top articles:", "top headlines:", "top news headlines:"}:
            headline_section_active = True
            continue

        if headline_section_active and (line.startswith("- ") or line.startswith("• ")):
            title = line[2:].strip()
            if title:
                headlines.append(title)
            if len(headlines) >= 3:
                headline_section_active = False
            continue

        if headline_section_active and line.startswith("  • "):
            title = line[4:].strip()
            if title:
                headlines.append(title)
            if len(headlines) >= 3:
                headline_section_active = False
            continue

    compact_lines: list[str] = []
    compact_lines.append(f"Provider used: {provider_used or 'NONE'}")
    compact_lines.append(f"Quality: {quality or 'N/A'}")
    compact_lines.append(f"Summary: {summary or 'N/A'}")

    if quality_reason:
        compact_lines.append(f"Reason: {_truncate_single_line(quality_reason, 180)}")

    compact_lines.append("")
    compact_lines.append("Top headlines:")
    if headlines:
        for title in headlines[:3]:
            compact_lines.append(f"- {title}")
    else:
        compact_lines.append("[dim]None[/dim]")

    return "\n".join(compact_lines).strip()


class RichVerboseReporter:
    """
    Rich-based implementation of VerboseReporter for console output.

    Provides human-readable progress updates and formatted panels
    during pipeline execution in verbose mode.
    """

    def __init__(self, console: Console) -> None:
        self.console = console

    def step_start(self, text: str) -> None:
        self.console.print(f"[cyan]→[/cyan] {text}")

    def step_done(self, text: str) -> None:
        self.console.print(f"[green]✓[/green] {text}")

    def panel(self, title: str, body: str) -> None:
        panel_body = body
        if "News Digest" in title and not _is_news_debug_enabled():
            compact = _compact_news_digest_body(body)
            if compact:
                panel_body = compact

        self.console.print()
        self.console.print(Panel(panel_body, title=title, border_style="blue"))
        self.console.print()

    def llm_summary(
        self,
        tech: str,
        news: str,
        synthesis: str,
        verify: str,
    ) -> None:
        summary_text = f"tech={tech} news={news} synthesis={synthesis} verify={verify}"
        self.console.print(f"[dim]LLM Summary:[/dim] {summary_text}")
