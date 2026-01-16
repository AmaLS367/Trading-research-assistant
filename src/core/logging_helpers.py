import time
from contextlib import contextmanager
from typing import Any

from src.utils.logging import get_logger

logger = get_logger(__name__)


def log_stage_start(stage: str, **extra: Any) -> None:
    """
    Log the start of a pipeline stage.

    Args:
        stage: Stage name (e.g., "fetch_candles", "tech_analysis")
        **extra: Additional context to log
    """
    extra_str = ", ".join(f"{k}={v}" for k, v in extra.items()) if extra else ""
    message = f"Stage start: {stage}"
    if extra_str:
        message += f" ({extra_str})"
    logger.debug(message)


def log_stage_end(stage: str, duration_ms: float, **extra: Any) -> None:
    """
    Log the end of a pipeline stage with duration.

    Args:
        stage: Stage name
        duration_ms: Duration in milliseconds
        **extra: Additional context to log
    """
    extra_str = ", ".join(f"{k}={v}" for k, v in extra.items()) if extra else ""
    message = f"Stage end: {stage}, duration={duration_ms:.1f}ms"
    if extra_str:
        message += f" ({extra_str})"
    logger.debug(message)


@contextmanager
def stage_timer(stage: str, **extra: Any):
    """
    Context manager for timing a pipeline stage.

    Usage:
        with stage_timer("fetch_candles", symbol="EURUSD"):
            # ... do work ...
    """
    start_time = time.time()
    log_stage_start(stage, **extra)
    try:
        yield
    finally:
        duration_ms = (time.time() - start_time) * 1000
        log_stage_end(stage, duration_ms, **extra)
