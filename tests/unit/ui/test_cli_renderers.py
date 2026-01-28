import json
from datetime import datetime

import pytest
from rich.console import Console

from src.core.models.recommendation import Recommendation
from src.core.models.timeframe import Timeframe
from src.ui.cli.renderers.synthesis_renderer import render_synthesis
from src.ui.cli.renderers.technical_renderer import render_technical_view

pytestmark = pytest.mark.unit


def _render_to_text(renderable: object) -> str:
    console = Console(record=True, width=120)
    console.print(renderable)
    return console.export_text()


def test_render_technical_view_valid_json() -> None:
    technical_json = json.dumps(
        {
            "bias": "BULLISH",
            "confidence": 0.82,
            "evidence": ["Trend up", "Momentum positive"],
            "contradictions": ["Near resistance"],
            "setup_type": "breakout",
            "no_trade_flags": ["SPREAD_TOO_WIDE"],
        }
    )

    panel = render_technical_view(technical_json)
    output = _render_to_text(panel)

    assert "Bias" in output
    assert "BULLISH" in output
    assert "Evidence" in output
    assert "Momentum positive" in output


def test_render_technical_view_fallback_on_broken_json() -> None:
    broken = '{"bias": "BULLISH", "confidence": 0.5,'
    panel = render_technical_view(broken)
    output = _render_to_text(panel)

    assert output.strip() != ""
    assert broken[:10] in output


def test_render_synthesis_renders_reason_codes_and_risks() -> None:
    recommendation = Recommendation(
        symbol="EURGBP",
        timestamp=datetime.now(),
        timeframe=Timeframe.M1,
        action="CALL",
        brief="Short brief",
        confidence=0.55,
        reason_codes=[],
    )

    extracted = json.dumps(
        {
            "action": "CALL",
            "confidence": 0.55,
            "brief": "Short brief",
            "reasons": ["Reason A", "Reason B"],
            "risks": ["Risk 1", "Risk 2"],
        }
    )

    debug_payload = {
        "parse_ok": True,
        "decision": {"reason_codes": ["LOW_VOLATILITY_NO_SQUEEZE", "WEAK_MOMENTUM"]},
        "extracted_json": extracted,
    }

    panel = render_synthesis(recommendation, json.dumps(debug_payload))
    output = _render_to_text(panel)

    assert "Reason codes" in output
    assert "LOW_VOLATILITY_NO_SQUEEZE" in output
    assert "Risks" in output
    assert "Risk 1" in output
