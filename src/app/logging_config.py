import logging
import re
import sys
from pathlib import Path
from types import FrameType
from typing import TYPE_CHECKING

from loguru import logger

if TYPE_CHECKING:
    from loguru import Record

from src.app.settings import settings


def sanitize_log_record(message: str) -> str:
    """
    Masks sensitive information in log messages.

    Masks:
    - Authorization headers (Bearer tokens, Basic auth)
    - API keys in URLs (apiKey=...)
    - Environment variable values for known API keys
    """
    if not settings.log_mask_auth:
        return message

    sanitized = message

    # Mask Authorization headers
    sanitized = re.sub(
        r"Authorization:\s*(?:Bearer|Basic)\s+[\w\-\.]+",
        "Authorization: *****",
        sanitized,
        flags=re.IGNORECASE,
    )

    # Mask apiKey=... in URLs
    sanitized = re.sub(
        r"apiKey=([^&\s]+)",
        "apiKey=*****",
        sanitized,
        flags=re.IGNORECASE,
    )

    # Mask known API key environment variable values
    api_key_patterns = [
        r"OPENAI_API_KEY[=:]\s*[\w\-]+",
        r"DEEPSEEK_API_KEY[=:]\s*[\w\-]+",
        r"GOOGLE_API_KEY[=:]\s*[\w\-]+",
        r"HF_TOKEN[=:]\s*[\w\-]+",
        r"HUGGINGFACE_HUB_TOKEN[=:]\s*[\w\-]+",
        r"NEWSAPI_API_KEY[=:]\s*[\w\-]+",
        r"OANDA_API_KEY[=:]\s*[\w\-]+",
        r"TWELVE_DATA_API_KEY[=:]\s*[\w\-]+",
    ]

    for pattern in api_key_patterns:
        sanitized = re.sub(
            pattern,
            lambda m: m.group(0).split("=")[0] + "=*****"
            if "=" in m.group(0)
            else m.group(0).split(":")[0] + ": *****",
            sanitized,
            flags=re.IGNORECASE,
        )

    return sanitized


class InterceptHandler(logging.Handler):
    """
    Intercepts standard logging records and forwards them to loguru.

    This allows existing code using standard logging to work with loguru
    without modification.
    """

    def emit(self, record: logging.LogRecord) -> None:
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = str(record.levelno)

        # Find the frame that called the logger, skipping logging module and this handler
        frame: FrameType | None = logging.currentframe()
        depth = 2
        while frame is not None:
            frame_filename = frame.f_code.co_filename
            # Skip frames from logging module and this handler
            if frame_filename == logging.__file__ or (
                frame.f_code.co_name == "emit" and "logging_config" in frame_filename
            ):
                frame = frame.f_back
                depth += 1
            else:
                break

        # Use record.name as the logger name by patching the record
        logger_opt = logger.opt(depth=depth, exception=record.exc_info)
        # Patch the record to use the original logger name
        def patcher(r: "Record") -> None:
            r["name"] = record.name

        logger_opt.patch(patcher).log(level, record.getMessage())


def should_filter_http_libs(record: "Record") -> bool:
    """
    Filter function to exclude httpx/httpcore logs from console output.

    Returns True if the record should be kept, False if it should be filtered out.
    """
    logger_name = record["name"]
    if logger_name is None:
        return True
    return not (logger_name.startswith("httpx") or logger_name.startswith("httpcore"))


def should_include_http_libs(record: "Record") -> bool:
    """
    Filter function to include only httpx/httpcore logs for http.log file.

    Returns True if the record should be kept, False if it should be filtered out.
    """
    logger_name = record["name"]
    if logger_name is None:
        return False
    return logger_name.startswith("httpx") or logger_name.startswith("httpcore")


def configure_logging(*, verbose: bool = False) -> None:
    """
    Configures loguru logging system.

    Sets up:
    - Console output with readable text format
    - File outputs (app.log, warnings.log, errors.log) with JSON format
    - Optional http.log for HTTP library logs
    - Intercepts standard logging and forwards to loguru
    - Masks sensitive information in logs
    - Filters out noisy library logs from console

    Args:
        verbose: If True, console level is set to DEBUG for application logs only
    """
    # Remove default loguru handler
    logger.remove()

    # Create log directory
    log_dir = Path(settings.log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)

    # Determine console level
    console_level = "DEBUG" if verbose else settings.log_console_level.upper()

    # Console sink with readable text format
    console_format = "{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}"
    logger.add(
        sys.stderr,
        format=console_format,
        level=console_level,
        filter=should_filter_http_libs,
        backtrace=False,
        diagnose=False,
        colorize=True,
    )

    # File sinks with JSON format
    # Use DEBUG level for files to capture all details for debugging
    file_level = "DEBUG"
    if settings.log_split_files:
        # app.log - DEBUG and above (for full debugging)
        logger.add(
            str(log_dir / "app.log"),
            format="{message}",
            level=file_level,
            rotation=settings.log_rotation,
            retention=settings.log_retention,
            compression=settings.log_compression,
            serialize=True,
            backtrace=True,
            diagnose=True,
        )

        # warnings.log - WARNING and above
        logger.add(
            str(log_dir / "warnings.log"),
            format="{message}",
            level="WARNING",
            rotation=settings.log_rotation,
            retention=settings.log_retention,
            compression=settings.log_compression,
            serialize=True,
            backtrace=True,
            diagnose=True,
        )

        # errors.log - ERROR and above
        logger.add(
            str(log_dir / "errors.log"),
            format="{message}",
            level="ERROR",
            rotation=settings.log_rotation,
            retention=settings.log_retention,
            compression=settings.log_compression,
            serialize=True,
            backtrace=True,
            diagnose=True,
        )
    else:
        # Single app.log file - DEBUG level for full debugging
        logger.add(
            str(log_dir / "app.log"),
            format="{message}",
            level=file_level,
            rotation=settings.log_rotation,
            retention=settings.log_retention,
            compression=settings.log_compression,
            serialize=True,
            backtrace=True,
            diagnose=True,
        )

    # Optional http.log for HTTP library logs
    if settings.log_enable_http_file:
        logger.add(
            str(log_dir / "http.log"),
            format="{message}",
            level=settings.log_http_level.upper(),
            rotation=settings.log_rotation,
            retention=settings.log_retention,
            compression=settings.log_compression,
            serialize=True,
            backtrace=True,
            diagnose=True,
            filter=should_include_http_libs,
        )

    # Intercept standard logging
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)

    # Set levels for noisy libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)

    # Apply sanitization via patcher
    def patcher(record: "Record") -> None:
        record["message"] = sanitize_log_record(record["message"])

    logger.patch(patcher)
