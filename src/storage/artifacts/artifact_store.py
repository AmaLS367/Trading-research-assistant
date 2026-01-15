import json
import re
from pathlib import Path
from typing import Any

from src.core.models.llm import LlmRequest, LlmResponse
from src.storage.artifacts.paths import ArtifactPaths


class ArtifactStore:
    def __init__(self, base_dir: Path) -> None:
        self.paths = ArtifactPaths(base_dir)

    def save_json(self, run_id: int, filename: str, data: dict[str, Any]) -> None:
        run_dir = self.paths.get_run_dir(run_id)
        self.paths.ensure_run_dir(run_id)
        file_path = run_dir / filename
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def save_text(self, run_id: int, filename: str, content: str) -> None:
        run_dir = self.paths.get_run_dir(run_id)
        self.paths.ensure_run_dir(run_id)
        file_path = run_dir / filename
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

    def _mask_secrets(self, data: dict[str, Any]) -> dict[str, Any]:
        masked = data.copy()
        for key, value in masked.items():
            if isinstance(value, str):
                if "api_key" in key.lower() or "apikey" in key.lower() or "token" in key.lower():
                    if value:
                        masked[key] = "***MASKED***"
                elif "base_url" in key.lower() or "url" in key.lower():
                    if value:
                        masked[key] = re.sub(r"(https?://[^/]+)(.*)", r"\1/***MASKED***", value)
            elif isinstance(value, dict):
                masked[key] = self._mask_secrets(value)
        return masked

    def save_llm_exchange(
        self, run_id: int, task: str, request: LlmRequest, response: LlmResponse
    ) -> None:
        llm_dir = self.paths.get_run_dir(run_id) / "llm" / task
        llm_dir.mkdir(parents=True, exist_ok=True)

        request_dict = {
            "task": request.task,
            "system_prompt": request.system_prompt,
            "user_prompt": request.user_prompt,
            "temperature": request.temperature,
            "timeout_seconds": request.timeout_seconds,
            "max_retries": request.max_retries,
            "model_name": request.model_name,
            "response_format": request.response_format,
        }
        masked_request = self._mask_secrets(request_dict)

        response_dict = {
            "text": response.text,
            "provider_name": response.provider_name,
            "model_name": response.model_name,
            "latency_ms": response.latency_ms,
            "attempts": response.attempts,
            "error": response.error,
        }

        request_path = llm_dir / "request.json"
        with open(request_path, "w", encoding="utf-8") as f:
            json.dump(masked_request, f, indent=2, ensure_ascii=False)

        response_path = llm_dir / "response.json"
        with open(response_path, "w", encoding="utf-8") as f:
            json.dump(response_dict, f, indent=2, ensure_ascii=False)

        response_text_path = llm_dir / "response.txt"
        with open(response_text_path, "w", encoding="utf-8") as f:
            f.write(response.text)
