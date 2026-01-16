#!/usr/bin/env python3
"""
Download LLM models for local use.

Supports downloading models from Hugging Face and optionally prefetching them in Ollama.
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from huggingface_hub import HfApi, snapshot_download  # noqa: E402
from huggingface_hub.utils.tqdm import enable_progress_bars  # noqa: E402

from src.app.settings import settings  # noqa: E402
from src.core.ports.llm_tasks import (  # noqa: E402
    TASK_NEWS_ANALYSIS,
    TASK_SYNTHESIS,
    TASK_TECH_ANALYSIS,
    TASK_VERIFICATION,
)


def get_hf_cache_dir() -> Path:
    """Get Hugging Face cache directory from environment or default.
    Priority order:
    1. HUGGINGFACE_HUB_CACHE (use as-is)
    2. HF_HOME -> HF_HOME/hub
    3. MODEL_STORAGE_DIR -> MODEL_STORAGE_DIR/.cache/huggingface/hub
    4. Default: ~/.cache/huggingface/hub (Windows: %USERPROFILE%\\.cache\\huggingface\\hub)
    """
    hf_hub_cache = os.environ.get("HUGGINGFACE_HUB_CACHE")
    if hf_hub_cache:
        cache_dir = Path(hf_hub_cache)
        cache_dir.mkdir(parents=True, exist_ok=True)
        return cache_dir

    hf_home = os.environ.get("HF_HOME")
    if hf_home:
        cache_dir = Path(hf_home) / "hub"
        cache_dir.mkdir(parents=True, exist_ok=True)
        return cache_dir

    model_storage_dir = os.environ.get("MODEL_STORAGE_DIR")
    if model_storage_dir:
        cache_dir = Path(model_storage_dir) / ".cache" / "huggingface" / "hub"
        cache_dir.mkdir(parents=True, exist_ok=True)
        return cache_dir

    default_cache = Path.home() / ".cache" / "huggingface" / "hub"
    default_cache.mkdir(parents=True, exist_ok=True)
    return default_cache


def get_hf_token() -> str | None:
    """Get Hugging Face token from environment variables.
    Priority: HF_TOKEN > HUGGINGFACE_HUB_TOKEN
    Returns None if no token is set.
    """
    token = os.environ.get("HF_TOKEN") or os.environ.get("HUGGINGFACE_HUB_TOKEN")
    return token if token else None


def get_hf_model_total_size_bytes(model_id: str, token: str | None) -> int | None:
    try:
        api = HfApi(token=token)
        info = api.model_info(repo_id=model_id)
        if not info.siblings:
            return None

        total = 0
        for sibling in info.siblings:
            size = getattr(sibling, "size", None)
            if isinstance(size, int):
                total += size

        return total if total > 0 else None
    except Exception:
        return None


def download_hf_model(model_id: str, hf_cache_dir: Path) -> bool:
    """Download a model from Hugging Face using huggingface_hub library."""
    try:
        token = get_hf_token()
        token_status = "yes" if token else "no"

        enable_progress_bars()

        total_bytes = get_hf_model_total_size_bytes(model_id=model_id, token=token)
        if total_bytes is not None:
            total_gb = total_bytes / (1024**3)
            print(f"Downloading {model_id} (~{total_gb:.2f} GB, token provided: {token_status})...")
        else:
            print(f"Downloading {model_id} (size unknown, token provided: {token_status})...")

        print(f"HF cache dir: {hf_cache_dir}")

        snapshot_download(
            repo_id=model_id,
            cache_dir=str(hf_cache_dir),
            token=token,
            local_files_only=False,
        )

        print(f"✓ Downloaded {model_id}")
        return True
    except Exception as e:
        print(f"✗ Failed to download {model_id}: {e}")
        return False


def ollama_list_models(base_url: str | None = None) -> set[str]:
    """List available models in Ollama."""
    try:
        cmd = ["ollama", "list"]
        env = os.environ.copy()
        if base_url:
            env["OLLAMA_HOST"] = base_url

        result = subprocess.run(cmd, check=True, capture_output=True, text=True, env=env)
        models: set[str] = set()
        for line in result.stdout.split("\n")[1:]:
            if line.strip():
                model_name = line.split()[0] if line.split() else ""
                if model_name:
                    models.add(model_name)
        return models
    except (subprocess.CalledProcessError, FileNotFoundError):
        return set()


def ollama_pull(model_name: str, base_url: str | None = None, dry_run: bool = False) -> bool:
    """Ensure model exists in Ollama. Pull if not present."""
    try:
        available_models = ollama_list_models(base_url)
        if model_name in available_models:
            print(f"INFO: ensure model {model_name} ok (already present)")
            return True

        if dry_run:
            print(f"INFO: would pull {model_name}")
            return True

        cmd = ["ollama", "pull", model_name]
        env = os.environ.copy()
        if base_url:
            env["OLLAMA_HOST"] = base_url

        result = subprocess.run(cmd, env=env)
        if result.returncode != 0:
            print(f"ERROR: Failed to pull {model_name} in Ollama (exit code: {result.returncode})")
            return False

        print(f"INFO: ensure model {model_name} ok (pulled)")
        return True
    except FileNotFoundError:
        print("ERROR: ollama command not found. Install Ollama from https://ollama.ai")
        return False


def collect_models_from_routing(profile: str = "small") -> tuple[set[str], set[str], set[str]]:
    """Collect all unique model names from routing configuration.
    Returns (ollama_local_models, ollama_server_models, hf_models) based on provider type.
    Skips API providers (deepseek_api, openai, google, etc.).
    Filters by profile and runtime_env.
    """
    ollama_local_models: set[str] = set()
    ollama_server_models: set[str] = set()
    hf_models: set[str] = set()

    from src.core.ports.llm_provider_name import (
        PROVIDER_OLLAMA_LOCAL,
        PROVIDER_OLLAMA_SERVER,
    )

    runtime_env = settings.runtime_env

    for task_name in [TASK_TECH_ANALYSIS, TASK_NEWS_ANALYSIS, TASK_SYNTHESIS, TASK_VERIFICATION]:
        candidates = settings.get_task_candidates(task_name)

        for candidate in candidates:
            provider = candidate.provider
            model = candidate.model

            if not model:
                continue

            if provider.endswith("_api") or provider in [
                "deepseek_api",
                "openai_api",
                "google_api",
            ]:
                print(f"INFO: skip api model {model} (provider: {provider})")
                continue

            if provider == PROVIDER_OLLAMA_LOCAL or provider.startswith("ollama_local"):
                if profile == "small" or runtime_env == "local":
                    ollama_local_models.add(model)
            elif provider == PROVIDER_OLLAMA_SERVER or provider.startswith("ollama_server"):
                if profile == "large" and runtime_env == "server":
                    ollama_server_models.add(model)
            elif provider == "hf_local" or provider.startswith("hf_"):
                hf_models.add(model)

    return ollama_local_models, ollama_server_models, hf_models


def check_ollama_server_available() -> tuple[bool, str | None]:
    """Check if Ollama server is available and valid."""
    if not settings.ollama_server_enabled:
        return False, "OLLAMA_SERVER_URL is not valid or disabled"
    server_url = settings._get_ollama_server_url()
    if not server_url:
        return False, "OLLAMA_SERVER_URL not configured"
    return True, None


def check_ollama_server_model(model_name: str) -> tuple[bool, str | None]:
    """Check if model exists on Ollama server. Returns (exists, error)."""
    try:
        import httpx

        server_url = settings._get_ollama_server_url()
        if not server_url:
            return False, "OLLAMA_SERVER_URL not configured"

        response = httpx.get(f"{server_url}/api/tags", timeout=10.0)
        if response.status_code != 200:
            return False, f"Server returned status {response.status_code}"

        data = response.json()
        models = data.get("models", [])
        for model in models:
            if model.get("name") == model_name:
                return True, None

        return False, None
    except Exception as e:
        return False, str(e)


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Download LLM models")
    parser.add_argument(
        "--hf-model",
        type=str,
        help="Hugging Face model ID to download (e.g., 'Qwen/Qwen2.5-7B-Instruct')",
    )
    parser.add_argument(
        "--ollama-model",
        type=str,
        help="Ollama model name to pull (e.g., 'qwen2.5:7b')",
    )
    parser.add_argument(
        "--from-routing",
        action="store_true",
        help="Download all models specified in routing configuration",
    )
    parser.add_argument(
        "--prefetch-ollama",
        action="store_true",
        help="After downloading HF models, also prefetch them in Ollama (if --from-routing is used)",
    )
    parser.add_argument(
        "--ollama-url",
        type=str,
        help="Ollama base URL (defaults to OLLAMA_LOCAL_URL or OLLAMA_BASE_URL)",
    )
    parser.add_argument(
        "--hf-cache-dir",
        type=str,
        help="Hugging Face cache directory (defaults to HF_HOME or XDG_CACHE_HOME)",
    )
    parser.add_argument(
        "--profile",
        type=str,
        choices=["small", "large"],
        default="small",
        help="Profile to use (default: small)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without actually downloading",
    )

    args = parser.parse_args()

    if not args.hf_model and not args.ollama_model and not args.from_routing:
        parser.print_help()
        return 1

    success = True

    if args.from_routing:
        ollama_local_models, ollama_server_models, hf_models = collect_models_from_routing(
            args.profile
        )
        total_models = len(ollama_local_models) + len(ollama_server_models) + len(hf_models)

        if total_models == 0:
            print("No models found in routing configuration for this profile")
            return 0 if args.dry_run else 1

        print(f"Found {total_models} unique model(s) in routing (profile: {args.profile}):")
        if ollama_local_models:
            print(f"  Ollama local models ({len(ollama_local_models)}):")
            for model in sorted(ollama_local_models):
                print(f"    - {model}")
        if ollama_server_models:
            print(f"  Ollama server models ({len(ollama_server_models)}):")
            for model in sorted(ollama_server_models):
                print(f"    - {model}")
        if hf_models:
            print(f"  Hugging Face models ({len(hf_models)}):")
            for model in sorted(hf_models):
                print(f"    - {model}")

        ollama_local_url = args.ollama_url
        if not ollama_local_url:
            ollama_local_url = settings._get_ollama_local_url()

        if ollama_local_models:
            print("\nEnsuring Ollama local models are available...")
            for model in sorted(ollama_local_models):
                if (
                    not ollama_pull(model, ollama_local_url, dry_run=args.dry_run)
                    and not args.dry_run
                ):
                    success = False

        if ollama_server_models:
            print("\nChecking Ollama server models...")
            server_available, server_error = check_ollama_server_available()
            if not server_available:
                print(f"WARNING: Ollama server not available: {server_error}")
                print("Skipping server models")
            else:
                for model in sorted(ollama_server_models):
                    exists, error = check_ollama_server_model(model)
                    if exists:
                        print(f"INFO: server model {model} ok (already present)")
                    else:
                        if error:
                            print(f"ERROR: server model {model} not found: {error}")
                            if not args.dry_run:
                                success = False
                        else:
                            print(f"WARNING: server model {model} not found on server")

        if hf_models:
            hf_cache = Path(args.hf_cache_dir) if args.hf_cache_dir else get_hf_cache_dir()
            print("\nDownloading Hugging Face models...")
            for model in sorted(hf_models):
                if args.dry_run:
                    print(f"INFO: would download {model}")
                else:
                    if not download_hf_model(model, hf_cache):
                        success = False

            if args.prefetch_ollama:
                print("\nPrefetching HF models in Ollama...")
                ollama_url = args.ollama_url
                if not ollama_url:
                    ollama_url = settings._get_ollama_local_url()

                for model in sorted(hf_models):
                    if (
                        not ollama_pull(model, ollama_url, dry_run=args.dry_run)
                        and not args.dry_run
                    ):
                        success = False

    if args.hf_model:
        hf_cache = Path(args.hf_cache_dir) if args.hf_cache_dir else get_hf_cache_dir()

        if not download_hf_model(args.hf_model, hf_cache):
            success = False

    if args.ollama_model:
        ollama_url = args.ollama_url
        if not ollama_url:
            ollama_url = settings._get_ollama_local_url()

        if (
            not ollama_pull(args.ollama_model, ollama_url, dry_run=args.dry_run)
            and not args.dry_run
        ):
            success = False

    if args.dry_run:
        return 0

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
