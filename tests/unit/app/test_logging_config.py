import logging
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

from src.app.logging_config import configure_logging, sanitize_log_record
from src.app.settings import get_settings


def test_sanitize_log_record_authorization_header():
    message = "Request headers: Authorization: Bearer sk-1234567890abcdef"
    sanitized = sanitize_log_record(message)
    assert "Authorization: Bearer sk-1234567890abcdef" not in sanitized
    assert "Authorization: *****" in sanitized


def test_sanitize_log_record_api_key_in_url():
    message = "Request URL: https://api.example.com/data?apiKey=secret123&param=value"
    sanitized = sanitize_log_record(message)
    assert "apiKey=secret123" not in sanitized
    assert "apiKey=*****" in sanitized


def test_sanitize_log_record_env_variable():
    message = "Config: OPENAI_API_KEY=sk-1234567890"
    sanitized = sanitize_log_record(message)
    assert "OPENAI_API_KEY=sk-1234567890" not in sanitized
    assert "OPENAI_API_KEY=*****" in sanitized


def test_sanitize_log_record_no_sensitive_data():
    message = "Normal log message without secrets"
    sanitized = sanitize_log_record(message)
    assert sanitized == message


def test_sanitize_log_record_disabled():
    with patch.dict(os.environ, {"LOG_MASK_AUTH": "false"}, clear=False):
        get_settings.cache_clear()
        message = "Request headers: Authorization: Bearer sk-1234567890abcdef"
        sanitized = sanitize_log_record(message)
        assert "Authorization: Bearer sk-1234567890abcdef" in sanitized
    get_settings.cache_clear()


def test_configure_logging_creates_directory():
    with tempfile.TemporaryDirectory() as tmpdir:
        log_dir = Path(tmpdir) / "test_logs"
        with patch.dict(os.environ, {"LOG_DIR": str(log_dir)}, clear=False):
            get_settings.cache_clear()
            configure_logging(verbose=False)
            assert log_dir.exists()
            assert log_dir.is_dir()
        get_settings.cache_clear()


def test_configure_logging_creates_files():
    with tempfile.TemporaryDirectory() as tmpdir:
        log_dir = Path(tmpdir) / "test_logs"
        with patch.dict(
            os.environ,
            {
                "LOG_DIR": str(log_dir),
                "LOG_SPLIT_FILES": "true",
            },
            clear=False,
        ):
            get_settings.cache_clear()
            configure_logging(verbose=False)
            assert (log_dir / "app.log").exists()
            assert (log_dir / "warnings.log").exists()
            assert (log_dir / "errors.log").exists()
        get_settings.cache_clear()


def test_configure_logging_http_file_when_enabled():
    with tempfile.TemporaryDirectory() as tmpdir:
        log_dir = Path(tmpdir) / "test_logs"
        with patch.dict(
            os.environ,
            {
                "LOG_DIR": str(log_dir),
                "LOG_ENABLE_HTTP_FILE": "true",
            },
            clear=False,
        ):
            get_settings.cache_clear()
            configure_logging(verbose=False)
            assert (log_dir / "http.log").exists()
        get_settings.cache_clear()


def test_configure_logging_no_http_file_when_disabled():
    with tempfile.TemporaryDirectory() as tmpdir:
        log_dir = Path(tmpdir) / "test_logs"
        with patch.dict(
            os.environ,
            {
                "LOG_DIR": str(log_dir),
                "LOG_ENABLE_HTTP_FILE": "false",
            },
            clear=False,
        ):
            get_settings.cache_clear()
            configure_logging(verbose=False)
            assert not (log_dir / "http.log").exists()
        get_settings.cache_clear()


def test_configure_logging_idempotent():
    with tempfile.TemporaryDirectory() as tmpdir:
        log_dir = Path(tmpdir) / "test_logs"
        with patch.dict(os.environ, {"LOG_DIR": str(log_dir)}, clear=False):
            get_settings.cache_clear()
            configure_logging(verbose=False)
            configure_logging(verbose=False)
            assert log_dir.exists()
        get_settings.cache_clear()


def test_configure_logging_sets_http_library_levels():
    with tempfile.TemporaryDirectory() as tmpdir:
        log_dir = Path(tmpdir) / "test_logs"
        with patch.dict(os.environ, {"LOG_DIR": str(log_dir)}, clear=False):
            get_settings.cache_clear()
            configure_logging(verbose=False)
            assert logging.getLogger("httpx").level == logging.WARNING
            assert logging.getLogger("httpcore").level == logging.WARNING
            assert logging.getLogger("urllib3").level == logging.WARNING
            assert logging.getLogger("asyncio").level == logging.WARNING
        get_settings.cache_clear()
