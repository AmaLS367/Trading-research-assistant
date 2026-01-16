"""Unit tests for download_models.py script."""

import os
from pathlib import Path
from unittest.mock import patch

import pytest


def test_get_hf_cache_dir_priority_huggingface_hub_cache(tmp_path: Path) -> None:
    """Test that HUGGINGFACE_HUB_CACHE has highest priority."""
    cache_path = tmp_path / "custom_cache"
    env_vars = {"HUGGINGFACE_HUB_CACHE": str(cache_path)}

    with patch.dict(os.environ, env_vars, clear=False):
        from scripts.python.download_models import get_hf_cache_dir

        result = get_hf_cache_dir()
        assert result == cache_path
        assert cache_path.exists()


def test_get_hf_cache_dir_priority_hf_home(tmp_path: Path) -> None:
    """Test that HF_HOME/hub is used when HUGGINGFACE_HUB_CACHE is not set."""
    hf_home = tmp_path / "hf_home"
    env_vars = {
        "HF_HOME": str(hf_home),
    }

    with patch.dict(os.environ, env_vars, clear=False):
        from scripts.python.download_models import get_hf_cache_dir

        result = get_hf_cache_dir()
        expected = hf_home / "hub"
        assert result == expected
        assert expected.exists()


def test_get_hf_cache_dir_priority_model_storage_dir(tmp_path: Path) -> None:
    """Test that MODEL_STORAGE_DIR/.cache/huggingface/hub is used as fallback."""
    model_storage = tmp_path / "model_storage"
    env_vars = {
        "MODEL_STORAGE_DIR": str(model_storage),
    }

    with patch.dict(os.environ, env_vars, clear=False):
        from scripts.python.download_models import get_hf_cache_dir

        result = get_hf_cache_dir()
        expected = model_storage / ".cache" / "huggingface" / "hub"
        assert result == expected
        assert expected.exists()


def test_get_hf_cache_dir_default(tmp_path: Path) -> None:
    """Test that default cache directory is used when no env vars are set."""
    with (
        patch.dict(os.environ, {}, clear=False),
        patch("scripts.python.download_models.Path.home", return_value=tmp_path),
    ):
        from scripts.python.download_models import get_hf_cache_dir

        result = get_hf_cache_dir()
        expected = tmp_path / ".cache" / "huggingface" / "hub"
        assert result == expected
        assert expected.exists()


def test_get_hf_token_from_hf_token() -> None:
    """Test that HF_TOKEN is preferred over HUGGINGFACE_HUB_TOKEN."""
    env_vars = {
        "HF_TOKEN": "hf_token_value",
        "HUGGINGFACE_HUB_TOKEN": "hub_token_value",
    }

    with patch.dict(os.environ, env_vars, clear=False):
        from scripts.python.download_models import get_hf_token

        result = get_hf_token()
        assert result == "hf_token_value"


def test_get_hf_token_from_huggingface_hub_token() -> None:
    """Test that HUGGINGFACE_HUB_TOKEN is used when HF_TOKEN is not set."""
    env_vars = {
        "HUGGINGFACE_HUB_TOKEN": "hub_token_value",
    }

    with patch.dict(os.environ, env_vars, clear=False):
        from scripts.python.download_models import get_hf_token

        result = get_hf_token()
        assert result == "hub_token_value"


def test_get_hf_token_returns_none_when_not_set() -> None:
    """Test that get_hf_token returns None when no token is set."""
    with patch.dict(os.environ, {}, clear=False):
        from scripts.python.download_models import get_hf_token

        result = get_hf_token()
        assert result is None


def test_download_hf_model_with_mock(tmp_path: Path) -> None:
    """Test download_hf_model with mocked snapshot_download."""
    cache_dir = tmp_path / "cache"
    model_id = "test/model"

    with patch("huggingface_hub.snapshot_download") as mock_download:
        mock_download.return_value = None

        from scripts.python.download_models import download_hf_model

        result = download_hf_model(model_id, cache_dir)

        assert result is True
        mock_download.assert_called_once_with(
            repo_id=model_id,
            cache_dir=str(cache_dir),
            token=None,
            local_files_only=False,
        )


def test_download_hf_model_with_token(tmp_path: Path) -> None:
    """Test download_hf_model with token from environment."""
    cache_dir = tmp_path / "cache"
    model_id = "test/model"
    env_vars = {"HF_TOKEN": "test_token"}

    with (
        patch.dict(os.environ, env_vars, clear=False),
        patch("huggingface_hub.snapshot_download") as mock_download,
    ):
        mock_download.return_value = None

        from scripts.python.download_models import download_hf_model

        result = download_hf_model(model_id, cache_dir)

        assert result is True
        mock_download.assert_called_once_with(
            repo_id=model_id,
            cache_dir=str(cache_dir),
            token="test_token",
            local_files_only=False,
        )


def test_download_hf_model_handles_import_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test download_hf_model handles ImportError gracefully."""
    cache_dir = tmp_path / "cache"
    model_id = "test/model"

    import sys
    from collections.abc import Sequence
    from types import ModuleType

    original_import = __import__

    def mock_import(
        name: str,
        globals: dict[str, object] | None = None,
        locals: dict[str, object] | None = None,
        fromlist: Sequence[str] = (),
        level: int = 0,
    ) -> ModuleType:
        if name == "huggingface_hub":
            raise ImportError("No module named 'huggingface_hub'")
        return original_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr("builtins.__import__", mock_import)

    if "huggingface_hub" in sys.modules:
        monkeypatch.delitem(sys.modules, "huggingface_hub", raising=False)

    from scripts.python.download_models import download_hf_model

    result = download_hf_model(model_id, cache_dir)
    assert result is False


def test_download_hf_model_handles_download_error(tmp_path: Path) -> None:
    """Test download_hf_model handles download errors gracefully."""
    cache_dir = tmp_path / "cache"
    model_id = "test/model"

    with patch("huggingface_hub.snapshot_download") as mock_download:
        mock_download.side_effect = Exception("Download failed")

        from scripts.python.download_models import download_hf_model

        result = download_hf_model(model_id, cache_dir)

        assert result is False
        mock_download.assert_called_once()


def test_download_hf_model_cache_dir_passed_correctly(tmp_path: Path) -> None:
    """Test that cache_dir from get_hf_cache_dir is passed correctly to snapshot_download."""
    custom_cache = tmp_path / "custom"
    env_vars = {"HUGGINGFACE_HUB_CACHE": str(custom_cache)}

    with (
        patch.dict(os.environ, env_vars, clear=False),
        patch("huggingface_hub.snapshot_download") as mock_download,
    ):
        mock_download.return_value = None

        from scripts.python.download_models import download_hf_model, get_hf_cache_dir

        cache_dir = get_hf_cache_dir()
        result = download_hf_model("test/model", cache_dir)

        assert result is True
        mock_download.assert_called_once()
        call_kwargs = mock_download.call_args[1]
        assert call_kwargs["cache_dir"] == str(custom_cache)
