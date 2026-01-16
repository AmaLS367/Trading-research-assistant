from unittest.mock import MagicMock

from src.core.pipeline_trace import PipelineTrace


def test_pipeline_trace_disabled():
    trace = PipelineTrace(enabled=False)
    mock_reporter = MagicMock()
    trace.reporter = mock_reporter
    trace.step_start("test")
    trace.step_done("test")
    trace.panel("title", "body")
    trace.llm_summary("tech", "news", "synthesis", "verify")
    mock_reporter.step_start.assert_not_called()
    mock_reporter.step_done.assert_not_called()
    mock_reporter.panel.assert_not_called()
    mock_reporter.llm_summary.assert_not_called()


def test_pipeline_trace_enabled():
    trace = PipelineTrace(enabled=True)
    mock_reporter = MagicMock()
    trace.reporter = mock_reporter
    trace.step_start("Fetching market data...")
    trace.step_done("Loaded 299 candles")
    trace.panel("Technical Rationale", "Analysis text")
    trace.llm_summary("ollama/llama3.2", "ollama/llama3.2", "ollama/llama3.2", "none")
    mock_reporter.step_start.assert_called_once_with("Fetching market data...")
    mock_reporter.step_done.assert_called_once_with("Loaded 299 candles")
    mock_reporter.panel.assert_called_once_with("Technical Rationale", "Analysis text")
    mock_reporter.llm_summary.assert_called_once_with(
        "ollama/llama3.2", "ollama/llama3.2", "ollama/llama3.2", "none"
    )


def test_pipeline_trace_emit_noop():
    trace = PipelineTrace(enabled=True)
    mock_reporter = MagicMock()
    trace.reporter = mock_reporter
    trace.emit("legacy message")
    mock_reporter.step_start.assert_not_called()
    mock_reporter.step_done.assert_not_called()
