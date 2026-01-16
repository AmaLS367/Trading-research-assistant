import io
from unittest.mock import patch

from src.core.pipeline_trace import PipelineTrace


def test_pipeline_trace_disabled():
    trace = PipelineTrace(enabled=False)
    # Capture stdout
    captured_output = io.StringIO()
    with patch("sys.stdout", captured_output):
        trace.emit("test | message")
    assert captured_output.getvalue() == ""


def test_pipeline_trace_enabled():
    trace = PipelineTrace(enabled=True)
    # Capture stdout
    captured_output = io.StringIO()
    with patch("sys.stdout", captured_output):
        trace.emit("candles | start | symbol=EURUSD timeframe=1h")
    output = captured_output.getvalue()
    assert "TRACE | candles | start | symbol=EURUSD timeframe=1h" in output


def test_pipeline_trace_format():
    trace = PipelineTrace(enabled=True)
    captured_output = io.StringIO()
    with patch("sys.stdout", captured_output):
        trace.emit("tech_llm | done | ok")
    output = captured_output.getvalue()
    assert output.strip() == "TRACE | tech_llm | done | ok"
