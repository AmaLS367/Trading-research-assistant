#!/usr/bin/env python3
"""
GPU and RAM profiling script for LLM model selection.

Checks available VRAM (GPU) and RAM to help determine which models can be run locally.
"""

import sys

try:
    import psutil
except ImportError:
    print("ERROR: psutil not installed. Install with: pip install psutil")
    sys.exit(1)

try:
    import pynvml
except ImportError:
    pynvml = None


def get_ram_info() -> dict[str, float]:
    """Get system RAM information in GB."""
    mem = psutil.virtual_memory()
    return {
        "total_gb": mem.total / (1024**3),
        "available_gb": mem.available / (1024**3),
        "used_gb": mem.used / (1024**3),
        "percent": mem.percent,
    }


def get_gpu_info() -> list[dict[str, float | int | str]] | None:
    """Get GPU VRAM information in GB. Returns None if no GPU or pynvml not available."""
    if pynvml is None:
        return None

    try:
        pynvml.nvmlInit()
        device_count = pynvml.nvmlDeviceGetCount()

        gpus: list[dict[str, float | int | str]] = []
        for i in range(device_count):
            handle = pynvml.nvmlDeviceGetHandleByIndex(i)
            name = pynvml.nvmlDeviceGetName(handle).decode("utf-8")

            mem_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
            total_gb = mem_info.total / (1024**3)
            used_gb = mem_info.used / (1024**3)
            free_gb = mem_info.free / (1024**3)

            gpus.append(
                {
                    "index": i,
                    "name": name,
                    "total_gb": total_gb,
                    "used_gb": used_gb,
                    "free_gb": free_gb,
                    "percent": (used_gb / total_gb) * 100 if total_gb > 0 else 0.0,
                }
            )

        return gpus
    except Exception:
        return None


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

    gpu_info = get_gpu_info()
    if gpu_info is None:
        print("GPU: Not available or pynvml not installed")
        print("  Install with: pip install nvidia-ml-py")
    else:
        print(f"GPU: {len(gpu_info)} device(s) found")
        for gpu in gpu_info:
            print(f"  GPU {gpu['index']}: {gpu['name']}")
            print(f"    Total VRAM: {format_size(gpu['total_gb'])}")
            print(f"    Used VRAM:  {format_size(gpu['used_gb'])} ({gpu['percent']:.1f}%)")
            print(f"    Free VRAM:  {format_size(gpu['free_gb'])}")
            print()

    print("=" * 60)
    print("Model Size Recommendations:")
    print("=" * 60)

    if gpu_info:
        min_free_vram = min(float(gpu["free_gb"]) for gpu in gpu_info)
        print(f"  Minimum free VRAM: {format_size(min_free_vram)}")
        if min_free_vram >= 24:
            print("  ✓ Can run: 32B+ models (qwen2.5:32b, llama3.1:70b)")
        elif min_free_vram >= 12:
            print("  ✓ Can run: 13B-16B models (llama3:70b quantized, qwen2.5:14b)")
        elif min_free_vram >= 6:
            print("  ✓ Can run: 7B-8B models (llama3:8b, qwen2.5:7b)")
        else:
            print("  ⚠ Limited VRAM. Consider smaller models or CPU-only mode.")
    else:
        available_ram = ram_info["available_gb"]
        print(f"  Available RAM: {format_size(available_ram)}")
        if available_ram >= 32:
            print("  ✓ Can run: 13B-16B models on CPU (slower)")
        elif available_ram >= 16:
            print("  ✓ Can run: 7B-8B models on CPU (slower)")
        else:
            print("  ⚠ Limited RAM. Consider API-based providers (DeepSeek API).")

    print()


def main() -> int:
    """Main entry point."""
    try:
        print_summary()
        return 0
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
