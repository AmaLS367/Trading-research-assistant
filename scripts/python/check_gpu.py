#!/usr/bin/env python3
"""
GPU and RAM profiling script for LLM model selection.

Checks available VRAM (GPU) and RAM to help determine which models can be run locally.
"""

import argparse
import json
import os
import subprocess
import sys

import psutil


def get_ram_info() -> dict[str, float]:
    """Get system RAM information in GB."""
    mem = psutil.virtual_memory()
    return {
        "total_gb": mem.total / (1024**3),
        "available_gb": mem.available / (1024**3),
        "used_gb": mem.used / (1024**3),
        "percent": mem.percent,
    }


def detect_gpu_nvidia_smi() -> tuple[dict[str, object] | None, str | None]:
    """Detect GPU using nvidia-smi command. Returns (gpu_dict, error)."""
    try:
        result = subprocess.run(
            [
                "nvidia-smi",
                "--query-gpu=name,memory.total,memory.used,memory.free",
                "--format=csv,noheader,nounits",
            ],
            capture_output=True,
            text=True,
            timeout=10,
            check=True,
        )

        lines = result.stdout.strip().split("\n")
        if not lines or not lines[0]:
            return None, "nvidia-smi returned empty output"

        first_line = lines[0].strip()
        parts = [p.strip() for p in first_line.split(",")]
        if len(parts) < 4:
            return None, f"nvidia-smi returned unexpected format: {first_line}"

        name = parts[0]
        total_mib = float(parts[1])
        used_mib = float(parts[2])
        free_mib = float(parts[3])

        total_gb = total_mib / 1024.0
        used_gb = used_mib / 1024.0
        free_gb = free_mib / 1024.0

        return {
            "vendor": "nvidia",
            "name": name,
            "total_vram_gb": total_gb,
            "used_vram_gb": used_gb,
            "free_vram_gb": free_gb,
        }, None

    except subprocess.CalledProcessError as e:
        return None, f"nvidia-smi failed: {e.stderr.strip()}"
    except FileNotFoundError:
        return None, "nvidia-smi not found in PATH"
    except subprocess.TimeoutExpired:
        return None, "nvidia-smi timeout"
    except Exception as e:
        return None, f"nvidia-smi error: {str(e)}"


def detect_gpu_torch() -> tuple[dict[str, object] | None, str | None]:
    """Detect GPU using torch.cuda. Returns (gpu_dict, error)."""
    try:
        import torch  # type: ignore[import-untyped]

        if not torch.cuda.is_available():
            return None, "torch.cuda.is_available() returned False"

        device_count = torch.cuda.device_count()
        if device_count == 0:
            return None, "torch.cuda.device_count() returned 0"

        device = torch.cuda.get_device_properties(0)
        name = device.name
        total_bytes = device.total_memory
        total_gb = total_bytes / (1024**3)

        return {
            "vendor": "nvidia",
            "name": name,
            "total_vram_gb": total_gb,
            "used_vram_gb": None,
            "free_vram_gb": None,
        }, None

    except ImportError:
        return None, "torch not installed"
    except Exception as e:
        return None, f"torch.cuda error: {str(e)}"


def detect_gpu() -> tuple[dict[str, object] | None, str, str | None]:
    """Detect GPU using primary (nvidia-smi) and fallback (torch) methods."""
    gpu, error = detect_gpu_nvidia_smi()
    if gpu is not None:
        return gpu, "nvidia_smi", None

    gpu, error = detect_gpu_torch()
    if gpu is not None:
        return gpu, "torch", None

    return None, "none", error


def format_size(gb: float) -> str:
    """Format GB size with 2 decimal places."""
    return f"{gb:.2f} GB"


def print_summary() -> None:
    """Print GPU and RAM summary."""
    print("=" * 60)
    print("GPU and RAM Profiling Report")
    print("=" * 60)
    print()

    ram_info = get_ram_info()
    print("System RAM:")
    print(f"  Total:     {format_size(ram_info['total_gb'])}")
    print(f"  Available: {format_size(ram_info['available_gb'])}")
    print(f"  Used:      {format_size(ram_info['used_gb'])} ({ram_info['percent']:.1f}%)")
    print()

    gpu, detect_method, detect_error = detect_gpu()
    if gpu is None:
        print("GPU: Not detected")
        if detect_error:
            print(f"  Error: {detect_error}")
        print(f"  Method: {detect_method}")
    else:
        gpu_name = str(gpu.get("name", "Unknown"))
        gpu_vendor = str(gpu.get("vendor", "Unknown"))
        print(f"GPU: {gpu_name} ({gpu_vendor})")
        total_vram = gpu.get("total_vram_gb")
        if isinstance(total_vram, (int, float)):
            print(f"  Total VRAM: {format_size(float(total_vram))}")
        used_vram = gpu.get("used_vram_gb")
        if isinstance(used_vram, (int, float)):
            print(f"  Used VRAM:  {format_size(float(used_vram))}")
        free_vram = gpu.get("free_vram_gb")
        if isinstance(free_vram, (int, float)):
            print(f"  Free VRAM:  {format_size(float(free_vram))}")
        print(f"  Detection method: {detect_method}")
        print()

    print("=" * 60)
    print("Model Size Recommendations:")
    print("=" * 60)

    threshold_gb = float(os.getenv("LOCAL_GPU_MIN_VRAM_GB", "8.0"))
    if gpu is not None:
        free_vram_val = gpu.get("free_vram_gb")
        if isinstance(free_vram_val, (int, float)):
            free_vram = float(free_vram_val)
            print(f"  Free VRAM: {format_size(free_vram)}")
            print(f"  Threshold: {format_size(threshold_gb)}")
            if free_vram >= threshold_gb:
                print("  ✓ Profile: large (can run larger models)")
            else:
                print("  ⚠ Profile: small (limited VRAM)")
    else:
        available_ram = ram_info["available_gb"]
        print(f"  Available RAM: {format_size(available_ram)}")
        print("  ⚠ Profile: small (no GPU detected)")

    print()


def get_summary_json() -> dict[str, object]:
    """Get GPU and RAM summary as JSON with required structure."""
    ram_info = get_ram_info()
    gpu, detect_method, detect_error = detect_gpu()

    threshold_gb = float(os.getenv("LOCAL_GPU_MIN_VRAM_GB", "8.0"))

    if gpu is not None and gpu.get("free_vram_gb") is not None:
        free_vram_val = gpu["free_vram_gb"]
        if isinstance(free_vram_val, (int, float)):
            free_vram = float(free_vram_val)
            min_free_vram = free_vram
            if free_vram >= threshold_gb:
                selected_profile = "large"
                selected_profile_reason = (
                    f"free_vram {free_vram:.1f} >= threshold {threshold_gb:.1f}"
                )
            else:
                selected_profile = "small"
                selected_profile_reason = (
                    f"free_vram {free_vram:.1f} < threshold {threshold_gb:.1f}"
                )
        else:
            min_free_vram = None
            selected_profile = "small"
            selected_profile_reason = "free_vram not available"
    else:
        min_free_vram = None
        selected_profile = "small"
        selected_profile_reason = "gpu not detected" if gpu is None else "free_vram not available"

    result: dict[str, object] = {
        "ram": ram_info,
        "gpu": gpu,
        "gpu_detect_method": detect_method,
        "gpu_detect_error": detect_error,
        "min_free_vram_gb": min_free_vram,
        "selected_profile": selected_profile,
        "selected_profile_reason": selected_profile_reason,
    }

    return result


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="GPU and RAM profiling script")
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON",
    )
    args = parser.parse_args()

    try:
        if args.json:
            result = get_summary_json()
            print(json.dumps(result, indent=2))
        else:
            print_summary()
        return 0
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
