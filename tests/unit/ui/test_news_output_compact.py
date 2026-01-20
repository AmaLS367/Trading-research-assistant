import pytest
from rich.console import Console

from src.ui.cli.verbose_reporter import RichVerboseReporter

pytestmark = pytest.mark.unit


def test_news_panel_is_compact_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("TRA_NEWS_DEBUG", raising=False)

    console = Console(record=True, width=120)
    reporter = RichVerboseReporter(console)

    heavy_body = "\n".join(
        [
            "Provider used: NONE",
            "Quality: LOW",
            "Summary: Quality LOW.",
            "Reason: Some very long quality reason that should be truncated if needed.",
            "Candidates: 75 total, 0 after filtering",
            "Pass Statistics:",
            "  strict: strict=0, medium=0, broad=0",
            "Top Queries:",
            '  pair_strict: (EURGBP OR "EUR/GBP") AND (forex OR fx)',
            "GDELT Diagnostics (top requests):",
            "  pair_strict: http_status=200, items_count=15",
            "Top News Headlines:",
            "- Headline 1",
            "- Headline 2",
            "- Headline 3",
            "- Headline 4",
            "- Headline 5",
        ]
    )

    reporter.panel("News Digest", heavy_body)
    output = console.export_text()

    assert "Provider used: NONE" in output
    assert "Quality: LOW" in output
    assert "Summary: Quality LOW." in output

    assert "GDELT Diagnostics" not in output
    assert "Top Queries" not in output
    assert "Pass Statistics" not in output
    assert "Candidates:" not in output

    assert "Headline 1" in output
    assert "Headline 2" in output
    assert "Headline 3" in output
    assert "Headline 4" not in output


def test_news_panel_shows_diagnostics_when_debug_enabled(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TRA_NEWS_DEBUG", "1")

    console = Console(record=True, width=120)
    reporter = RichVerboseReporter(console)

    body = "Provider used: NONE\nGDELT Diagnostics (top requests):\n  pair_strict: http_status=200"
    reporter.panel("News Digest", body)
    output = console.export_text()

    assert "GDELT Diagnostics (top requests):" in output
