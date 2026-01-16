from unittest.mock import MagicMock, patch

from loguru import logger

from src.app.settings import settings
from src.runtime.preflight import run_preflight


def test_preflight_successful_gpu_check_and_download():
    with patch("subprocess.run") as mock_run:
        mock_check_gpu = MagicMock()
        mock_check_gpu.returncode = 0
        mock_check_gpu.stdout = "Minimum free VRAM: 12.5 GB"
        mock_check_gpu.stderr = ""

        mock_download = MagicMock()
        mock_download.returncode = 0
        mock_download.stdout = "Download complete"
        mock_download.stderr = ""

        mock_run.side_effect = [mock_check_gpu, mock_download]

        with patch("pathlib.Path.exists", return_value=True):
            run_preflight(settings, logger, verbose=False)

        assert mock_run.call_count == 2
        assert "--from-routing" in str(mock_run.call_args_list[1])


def test_preflight_gpu_check_fails_does_not_call_download():
    with patch("subprocess.run") as mock_run:
        mock_check_gpu = MagicMock()
        mock_check_gpu.returncode = 1
        mock_check_gpu.stdout = ""
        mock_check_gpu.stderr = "GPU check failed"

        mock_run.return_value = mock_check_gpu

        with patch("pathlib.Path.exists", return_value=True):
            run_preflight(settings, logger, verbose=False)

        assert mock_run.call_count == 1
        assert "--from-routing" not in str(mock_run.call_args)


def test_preflight_scripts_not_found_continues_safely():
    with patch("subprocess.run") as mock_run:
        with patch("pathlib.Path.exists", return_value=False):
            run_preflight(settings, logger, verbose=False)

        mock_run.assert_not_called()


def test_preflight_timeout_continues_safely():
    from subprocess import TimeoutExpired

    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = TimeoutExpired("check_gpu.py", 60)

        with patch("pathlib.Path.exists", return_value=True):
            run_preflight(settings, logger, verbose=False)

        assert mock_run.call_count == 1


def test_preflight_download_fails_continues_safely():
    with patch("subprocess.run") as mock_run:
        mock_check_gpu = MagicMock()
        mock_check_gpu.returncode = 0
        mock_check_gpu.stdout = "Minimum free VRAM: 12.5 GB"
        mock_check_gpu.stderr = ""

        mock_download = MagicMock()
        mock_download.returncode = 1
        mock_download.stdout = ""
        mock_download.stderr = "Download failed"

        mock_run.side_effect = [mock_check_gpu, mock_download]

        with patch("pathlib.Path.exists", return_value=True):
            run_preflight(settings, logger, verbose=False)

        assert mock_run.call_count == 2
