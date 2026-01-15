import json
import tempfile
from pathlib import Path

from src.core.models.llm import LlmRequest, LlmResponse
from src.storage.artifacts.artifact_store import ArtifactStore


def test_save_llm_exchange_creates_files():
    with tempfile.TemporaryDirectory() as tmpdir:
        artifacts_dir = Path(tmpdir)
        artifact_store = ArtifactStore(artifacts_dir)

        request = LlmRequest(
            task="tech_analysis",
            system_prompt="You are an expert",
            user_prompt="Analyze this",
            temperature=0.2,
            timeout_seconds=60.0,
            max_retries=1,
            model_name="test-model",
        )

        response = LlmResponse(
            text="Analysis result",
            provider_name="test_provider",
            model_name="test-model",
            latency_ms=100,
            attempts=1,
            error=None,
        )

        artifact_store.save_llm_exchange(1, "tech_analysis", request, response)

        llm_dir = artifacts_dir / "run_1" / "llm" / "tech_analysis"
        assert llm_dir.exists()

        request_file = llm_dir / "request.json"
        assert request_file.exists()

        response_file = llm_dir / "response.json"
        assert response_file.exists()

        response_text_file = llm_dir / "response.txt"
        assert response_text_file.exists()

        with open(request_file, encoding="utf-8") as f:
            request_data = json.load(f)
            assert request_data["task"] == "tech_analysis"
            assert request_data["system_prompt"] == "You are an expert"

        with open(response_file, encoding="utf-8") as f:
            response_data = json.load(f)
            assert response_data["text"] == "Analysis result"
            assert response_data["provider_name"] == "test_provider"

        with open(response_text_file, encoding="utf-8") as f:
            assert f.read() == "Analysis result"


def test_save_llm_exchange_masks_secrets():
    with tempfile.TemporaryDirectory() as tmpdir:
        artifacts_dir = Path(tmpdir)
        artifact_store = ArtifactStore(artifacts_dir)

        request_dict = {
            "task": "test",
            "system_prompt": "test",
            "user_prompt": "test",
            "temperature": 0.2,
            "timeout_seconds": 60.0,
            "max_retries": 1,
            "api_key": "secret-key-123",
            "base_url": "https://api.example.com/v1",
        }

        masked = artifact_store._mask_secrets(request_dict)

        assert masked["api_key"] == "***MASKED***"
        assert "***MASKED***" in masked["base_url"]
        assert "https://api.example.com" in masked["base_url"]
