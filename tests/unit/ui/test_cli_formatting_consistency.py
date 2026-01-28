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


def test_technical_renderer_normalizes_bias_and_formats_confidence_percent() -> None:
    technical_json = json.dumps(
        {
            "bias": "bullish",
            "confidence": 0.5555,
            "evidence": ["A" * 500],
            "contradictions": ["Line1\nLine2"],
            "setup_type": "setup-name",
            "no_trade_flags": [],
        }
    )

    text_1 = _render_to_text(render_technical_view(technical_json))
    text_2 = _render_to_text(render_technical_view(technical_json))

    assert text_1 == text_2
    assert "Bias: BULLISH" in text_1
    assert "Confidence: 55.55%" in text_1
    assert "(truncated)" in text_1
    assert "Line1 Line2" in text_1


def test_synthesis_renderer_normalizes_action_and_preserves_list_order() -> None:
    recommendation = Recommendation(
        symbol="EURGBP",
        timestamp=datetime.now(),
        timeframe=Timeframe.M1,
        action="call",
        brief="Brief line",
        confidence=0.1234,
        reason_codes=["Z_CODE", "A_CODE"],
    )

    extracted = json.dumps(
        {
            "action": "CALL",
            "confidence": 0.1234,
            "brief": "Brief line",
            "reasons": ["Reason B", "Reason A"],
            "risks": ["Risk B", "Risk A"],
        }
    )

    debug_payload = {
        "parse_ok": True,
        "decision": {"reason_codes": ["Z_CODE", "A_CODE"]},
        "extracted_json": extracted,
    }

    text_1 = _render_to_text(render_synthesis(recommendation, json.dumps(debug_payload)))
    text_2 = _render_to_text(render_synthesis(recommendation, json.dumps(debug_payload)))

    assert text_1 == text_2
    assert "Action: CALL" in text_1
    assert "Confidence: 12.34%" in text_1
    assert "Reason codes: Z_CODE, A_CODE" in text_1

    assert text_1.index("• Reason B") < text_1.index("• Reason A")
    assert text_1.index("• Risk B") < text_1.index("• Risk A")
