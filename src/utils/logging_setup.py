from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any

from src.app.logging_config import sanitize_log_record
from src.app.settings import settings

STANDARD_LOG_RECORD_KEYS = {
    "args",
    "asctime",
    "created",
    "exc_info",
    "exc_text",
    "filename",
    "funcName",
    "levelname",
    "levelno",
    "lineno",
    "module",
    "msecs",
    "message",
    "msg",
    "name",
    "pathname",
    "process",
    "processName",
    "relativeCreated",
    "stack_info",
    "thread",
    "threadName",
}


def _safe_json_value(value: Any) -> Any:
    try:
        json.dumps(value)
        return value
    except Exception:
        return str(value)


class JsonLinesFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        message = sanitize_log_record(record.getMessage())
        payload: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, tz=UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": message,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "process": record.process,
            "thread": record.threadName,
        }

        for key, value in record.__dict__.items():
            if key in STANDARD_LOG_RECORD_KEYS:
                continue
            payload[key] = _safe_json_value(value)

        if record.exc_info:
            payload["traceback"] = self.formatException(record.exc_info)

        return json.dumps(payload, ensure_ascii=False)


def _filter_extra(extra: dict[str, Any]) -> dict[str, Any]:
    filtered: dict[str, Any] = {}
    for key, value in extra.items():
        if key in STANDARD_LOG_RECORD_KEYS:
            continue
        filtered[key] = value
    return filtered


def _loguru_to_std_logging_sink(message: Any) -> None:
    record = message.record
    logger_name = record.get("name", "loguru")
    std_logger = logging.getLogger(logger_name)

    extra: dict[str, Any] = _filter_extra(record.get("extra", {}))
    extra.update(
        {
            "source_file": record.get("file").path if record.get("file") else None,
            "source_function": record.get("function"),
            "source_line": record.get("line"),
        }
    )

    exception = record.get("exception")
    if exception is not None:
        std_logger.log(
            record["level"].no,
            record.get("message", ""),
            extra=extra,
            exc_info=(exception.type, exception.value, exception.traceback),
        )
        return

    std_logger.log(record["level"].no, record.get("message", ""), extra=extra)


def setup_logging(*, verbose: bool = False) -> None:
    """
    Configure logging with:
    - Rich console handler (INFO+)
    - Rotating file handler (DEBUG+) for logs/app.log with JSON lines
    - Loguru forwarding into standard logging (for preflight + any loguru usage)
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    log_dir = Path(getattr(settings, "log_dir", "logs"))
    log_dir.mkdir(parents=True, exist_ok=True)

    app_file_handler = RotatingFileHandler(
        filename=str(log_dir / "app.log"),
        maxBytes=5 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    app_file_handler.setLevel(logging.DEBUG)
    app_file_handler.setFormatter(JsonLinesFormatter())
    root_logger.addHandler(app_file_handler)

    warnings_file_handler = RotatingFileHandler(
        filename=str(log_dir / "warnings.log"),
        maxBytes=5 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    warnings_file_handler.setLevel(logging.WARNING)
    warnings_file_handler.setFormatter(JsonLinesFormatter())
    root_logger.addHandler(warnings_file_handler)

    errors_file_handler = RotatingFileHandler(
        filename=str(log_dir / "errors.log"),
        maxBytes=5 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    errors_file_handler.setLevel(logging.ERROR)
    errors_file_handler.setFormatter(JsonLinesFormatter())
    root_logger.addHandler(errors_file_handler)

    console_level = logging.INFO
    console_handler: logging.Handler
    try:
        from rich.logging import RichHandler

        console_handler = RichHandler(
            level=console_level,
            show_time=False,
            show_level=False,
            show_path=False,
            rich_tracebacks=False,
            markup=True,
        )
        console_handler.setFormatter(logging.Formatter("%(message)s"))
    except Exception:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(console_level)
        console_handler.setFormatter(logging.Formatter("%(message)s"))

    root_logger.addHandler(console_handler)

    logging.captureWarnings(True)

    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)

    try:
        from loguru import logger as loguru_logger

        loguru_logger.remove()
        loguru_logger.add(_loguru_to_std_logging_sink, level="DEBUG")
    except Exception:
        pass
