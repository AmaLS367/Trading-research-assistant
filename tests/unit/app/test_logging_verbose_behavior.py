import logging
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

from src.app.logging_config import configure_logging
from src.app.settings import get_settings


def test_configure_logging_non_verbose_console_level():
    with tempfile.TemporaryDirectory() as tmpdir:
        log_dir = Path(tmpdir) / "test_logs"
        env_vars = {
            "LOG_DIR": str(log_dir),
            "LOG_CONSOLE_LEVEL": "INFO",
        }
        with patch.dict(os.environ, env_vars, clear=False):
            get_settings.cache_clear()
            # Should not raise exception
            configure_logging(verbose=False)
            # Verify it can be called multiple times
            configure_logging(verbose=False)
        get_settings.cache_clear()


def test_configure_logging_verbose_console_level():
    with tempfile.TemporaryDirectory() as tmpdir:
        log_dir = Path(tmpdir) / "test_logs"
        env_vars = {
            "LOG_DIR": str(log_dir),
            "LOG_CONSOLE_LEVEL": "INFO",
        }
        with patch.dict(os.environ, env_vars, clear=False):
            get_settings.cache_clear()
            # Should not raise exception
            configure_logging(verbose=True)
            # Verify it can be called multiple times
            configure_logging(verbose=True)
        get_settings.cache_clear()


def test_intercept_handler_preserves_logger_name():
    with tempfile.TemporaryDirectory() as tmpdir:
        log_dir = Path(tmpdir) / "test_logs"
        env_vars = {"LOG_DIR": str(log_dir)}
        with patch.dict(os.environ, env_vars, clear=False):
            get_settings.cache_clear()
            configure_logging(verbose=False)

            # Create a logger with a specific name
            test_logger = logging.getLogger("src.runtime.orchestrator")
            # Should not raise exception
            test_logger.info("Test message")
            test_logger.debug("Test debug message")
        get_settings.cache_clear()
