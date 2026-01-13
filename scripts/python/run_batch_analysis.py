"""Batch analysis script for multiple currency pairs."""
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

SYMBOLS = [
    "EURUSD",
    "GBPUSD",
    "USDJPY",
    "AUDUSD",
    "USDCAD",
    "USDCHF",
    "EURJPY",
    "GBPJPY",
    "NZDUSD",
    "EURCAD",
    "GBPCAD",
    "BTCUSD",
    "ETHUSD",
]

TIMEFRAME = "1m"
OUTPUT_FILE = Path("batch_analysis_output.txt")


def run_analysis(symbol: str) -> tuple[str, str, int]:
    """Run analysis for a symbol and return stdout, stderr, and return code."""
    import shutil
    
    uv_cmd = shutil.which("uv")
    if uv_cmd:
        cmd = [
            uv_cmd,
            "run",
            "python",
            "-m",
            "src.app.main",
            "analyze",
            "--symbol",
            symbol,
            "--timeframe",
            TIMEFRAME,
            "--verbose",
        ]
    else:
        cmd = [
            sys.executable,
            "-m",
            "src.app.main",
            "analyze",
            "--symbol",
            symbol,
            "--timeframe",
            TIMEFRAME,
            "--verbose",
        ]
    
    try:
        env = dict(os.environ)
        env["PYTHONIOENCODING"] = "utf-8"
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,
            env=env,
            encoding="utf-8",
            errors="replace",
        )
        return result.stdout, result.stderr, result.returncode
    except subprocess.TimeoutExpired:
        return "", "Timeout after 300 seconds", 1
    except Exception as e:
        return "", str(e), 1


def main() -> None:
    """Run batch analysis for all symbols."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(f"Batch Analysis Report\n")
        f.write(f"Started: {timestamp}\n")
        f.write(f"Timeframe: {TIMEFRAME}\n")
        f.write(f"Total symbols: {len(SYMBOLS)}\n")
        f.write("=" * 80 + "\n\n")
        
        for i, symbol in enumerate(SYMBOLS, 1):
            print(f"[{i}/{len(SYMBOLS)}] Analyzing {symbol}...", flush=True)
            
            f.write(f"\n{'=' * 80}\n")
            f.write(f"Symbol: {symbol}\n")
            f.write(f"Timeframe: {TIMEFRAME}\n")
            f.write(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"{'=' * 80}\n\n")
            
            stdout, stderr, returncode = run_analysis(symbol)
            
            if returncode == 0:
                f.write("STDOUT:\n")
                f.write(stdout)
                f.write("\n")
            else:
                f.write(f"ERROR (return code: {returncode}):\n")
                f.write(stderr)
                f.write("\n")
            
            if stderr:
                f.write("STDERR:\n")
                f.write(stderr)
                f.write("\n")
            
            f.write("\n" + "-" * 80 + "\n\n")
            f.flush()
        
        end_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        f.write(f"\n{'=' * 80}\n")
        f.write(f"Batch Analysis Completed\n")
        f.write(f"Ended: {end_timestamp}\n")
        f.write(f"{'=' * 80}\n")
    
    print(f"\nAnalysis complete! Results saved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
