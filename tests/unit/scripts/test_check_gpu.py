"""Unit tests for check_gpu.py script."""

from unittest.mock import MagicMock, patch

import pytest


def test_detect_gpu_nvidia_smi_parses_csv_correctly() -> None:
    """Test that nvidia-smi CSV output is parsed correctly."""
    from scripts.python.check_gpu import detect_gpu_nvidia_smi

    mock_result = MagicMock()
    mock_result.stdout = "NVIDIA GeForce RTX 3050 Laptop GPU, 4096, 0, 4096\n"
    mock_result.returncode = 0
    mock_result.stderr = ""

    with patch("subprocess.run", return_value=mock_result):
        gpu, error = detect_gpu_nvidia_smi()

        assert error is None
        assert gpu is not None
        assert gpu["vendor"] == "nvidia"
        assert gpu["name"] == "NVIDIA GeForce RTX 3050 Laptop GPU"
        assert gpu["total_vram_gb"] == pytest.approx(4.0, rel=0.01)
        assert gpu["used_vram_gb"] == pytest.approx(0.0, rel=0.01)
        assert gpu["free_vram_gb"] == pytest.approx(4.0, rel=0.01)


def test_detect_gpu_nvidia_smi_handles_file_not_found() -> None:
    """Test that FileNotFoundError is handled correctly."""
    from scripts.python.check_gpu import detect_gpu_nvidia_smi

    with patch("subprocess.run", side_effect=FileNotFoundError()):
        gpu, error = detect_gpu_nvidia_smi()

        assert gpu is None
        assert error == "nvidia-smi not found in PATH"


def test_detect_gpu_nvidia_smi_handles_invalid_format() -> None:
    """Test that invalid CSV format is handled correctly."""
    from scripts.python.check_gpu import detect_gpu_nvidia_smi

    mock_result = MagicMock()
    mock_result.stdout = "Invalid,Format\n"
    mock_result.returncode = 0
    mock_result.stderr = ""

    with patch("subprocess.run", return_value=mock_result):
        gpu, error = detect_gpu_nvidia_smi()

        assert gpu is None
        assert error is not None
        assert "unexpected format" in error.lower() or "parse error" in error.lower()


def test_detect_gpu_nvidia_smi_handles_empty_output() -> None:
    """Test that empty output is handled correctly."""
    from scripts.python.check_gpu import detect_gpu_nvidia_smi

    mock_result = MagicMock()
    mock_result.stdout = ""
    mock_result.returncode = 0
    mock_result.stderr = ""

    with patch("subprocess.run", return_value=mock_result):
        gpu, error = detect_gpu_nvidia_smi()

        assert gpu is None
        assert error is not None
        assert "empty" in error.lower()


def test_get_summary_json_always_returns_all_fields() -> None:
    """Test that get_summary_json always returns all required fields."""
    from scripts.python.check_gpu import get_summary_json

    with patch("scripts.python.check_gpu.detect_gpu", return_value=(None, "none", "test error")):
        result = get_summary_json()

        assert "ram" in result
        assert "gpu" in result
        assert "gpu_detect_method" in result
        assert "gpu_detect_error" in result
        assert "min_free_vram_gb" in result
        assert "selected_profile" in result
        assert "selected_profile_reason" in result

        assert result["gpu"] is None
        assert result["gpu_detect_method"] == "none"
        assert result["gpu_detect_error"] == "test error"
        assert result["selected_profile"] == "small"


def test_get_summary_json_with_gpu() -> None:
    """Test that get_summary_json works correctly with GPU detected."""
    from scripts.python.check_gpu import get_summary_json

    gpu_dict = {
        "vendor": "nvidia",
        "name": "Test GPU",
        "total_vram_gb": 8.0,
        "used_vram_gb": 2.0,
        "free_vram_gb": 6.0,
    }

    with (
        patch("scripts.python.check_gpu.detect_gpu", return_value=(gpu_dict, "nvidia_smi", None)),
        patch.dict("os.environ", {"LOCAL_GPU_MIN_VRAM_GB": "8.0"}),
    ):
        result = get_summary_json()

        assert result["gpu"] == gpu_dict
        assert result["gpu_detect_method"] == "nvidia_smi"
        assert result["gpu_detect_error"] is None
        assert result["min_free_vram_gb"] == 6.0
        assert result["selected_profile"] == "small"
        reason = str(result["selected_profile_reason"])
        assert "free_vram 6.0 < threshold 8.0" in reason
