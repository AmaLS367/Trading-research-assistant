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

from src.app.settings import settings
from src.core.ports.llm_tasks import (
    TASK_NEWS_ANALYSIS,
    TASK_SYNTHESIS,
    TASK_TECH_ANALYSIS,
    TASK_VERIFICATION,
)


def get_hf_cache_dir() -> Path | None:
    """Get Hugging Face cache directory from environment or default."""
    hf_home = os.environ.get("HF_HOME")
    if hf_home:
        return Path(hf_home) / "hub"

    cache_home = os.environ.get("XDG_CACHE_HOME")
    if cache_home:
        return Path(cache_home) / "huggingface" / "hub"

    if sys.platform == "win32":
        default_cache = Path.home() / ".cache" / "huggingface" / "hub"
    else:
        default_cache = Path.home() / ".cache" / "huggingface" / "hub"

    return default_cache if default_cache.exists() else None


def download_hf_model(model_id: str, hf_cache_dir: Path | None) -> bool:
    """Download a model from Hugging Face using huggingface-cli."""
    try:
        cmd = ["huggingface-cli", "download", model_id]
        if hf_cache_dir:
            cmd.extend(["--cache-dir", str(hf_cache_dir)])

        subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(f"✓ Downloaded {model_id}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to download {model_id}: {e.stderr}")
        return False
    except FileNotFoundError:
        print("✗ huggingface-cli not found. Install with: pip install huggingface-hub")
        return False


def ollama_pull(model_name: str, base_url: str | None = None) -> bool:
    """Pull a model in Ollama."""
    try:
        cmd = ["ollama", "pull", model_name]
        if base_url:
            os.environ["OLLAMA_HOST"] = base_url

        subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(f"✓ Pulled {model_name} in Ollama")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to pull {model_name} in Ollama: {e.stderr}")
        return False
    except FileNotFoundError:
        print("✗ ollama command not found. Install Ollama from https://ollama.ai")
        return False


def collect_models_from_routing() -> tuple[set[str], set[str]]:
    """Collect all unique model names from routing configuration.
    Returns (ollama_models, hf_models) based on provider type.
    """
    ollama_models: set[str] = set()
    hf_models: set[str] = set()

    from src.core.ports.llm_provider_name import (
        PROVIDER_OLLAMA_LOCAL,
        PROVIDER_OLLAMA_SERVER,
    )

    for task_name in [TASK_TECH_ANALYSIS, TASK_NEWS_ANALYSIS, TASK_SYNTHESIS, TASK_VERIFICATION]:
        if task_name == TASK_TECH_ANALYSIS:
            routing = settings.get_tech_routing()
        elif task_name == TASK_NEWS_ANALYSIS:
            routing = settings.get_news_routing()
        elif task_name == TASK_SYNTHESIS:
            routing = settings.get_synthesis_routing()
        else:
            routing = settings.get_verifier_routing()

        for step in routing.steps:
            if step.model:
                if step.provider in [PROVIDER_OLLAMA_LOCAL, PROVIDER_OLLAMA_SERVER]:
                    ollama_models.add(step.model)
                else:
                    hf_models.add(step.model)

    return ollama_models, hf_models


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

    args = parser.parse_args()

    if not args.hf_model and not args.ollama_model and not args.from_routing:
        parser.print_help()
        return 1

    success = True

    if args.from_routing:
        ollama_models, hf_models = collect_models_from_routing()
        total_models = len(ollama_models) + len(hf_models)

        if total_models == 0:
            print("No models found in routing configuration")
            return 1

        print(f"Found {total_models} unique model(s) in routing:")
        if ollama_models:
            print(f"  Ollama models ({len(ollama_models)}):")
            for model in sorted(ollama_models):
                print(f"    - {model}")
        if hf_models:
            print(f"  Hugging Face models ({len(hf_models)}):")
            for model in sorted(hf_models):
                print(f"    - {model}")

        ollama_url = args.ollama_url
        if not ollama_url:
            ollama_url = settings._get_ollama_local_url()

        if ollama_models:
            print("\nPulling Ollama models...")
            for model in sorted(ollama_models):
                if not ollama_pull(model, ollama_url):
                    success = False

        if hf_models:
            hf_cache = Path(args.hf_cache_dir) if args.hf_cache_dir else get_hf_cache_dir()
            print("\nDownloading Hugging Face models...")
            for model in sorted(hf_models):
                if not download_hf_model(model, hf_cache):
                    success = False

            if args.prefetch_ollama:
                print("\nPrefetching HF models in Ollama...")
                ollama_url = args.ollama_url
                if not ollama_url:
                    ollama_url = settings._get_ollama_local_url()

                for model in sorted(hf_models):
                    if not ollama_pull(model, ollama_url):
                        success = False

    if args.hf_model:
        hf_cache = Path(args.hf_cache_dir) if args.hf_cache_dir else get_hf_cache_dir()

        if not download_hf_model(args.hf_model, hf_cache):
            success = False

    if args.ollama_model:
        ollama_url = args.ollama_url
        if not ollama_url:
            ollama_url = settings._get_ollama_local_url()

        if not ollama_pull(args.ollama_model, ollama_url):
            success = False

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
