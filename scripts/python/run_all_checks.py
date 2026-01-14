"""Run all code quality checks."""
import subprocess
import sys
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


def find_command(cmd: str) -> str | None:
    """Find command in PATH or try uv run."""
    import shutil

    if shutil.which(cmd):
        return cmd

    if shutil.which("uv"):
        return f"uv run {cmd}"

    return None


def run_command(cmd: str, description: str, stop_on_error: bool = False) -> tuple[bool, str]:
    """Run a command and return success status and output."""
    console.print(f"\n[bold blue]Running: {description}[/bold blue]")

    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=300,
        )

        if result.returncode == 0:
            console.print(f"[green]✓[/green] {description} passed")
            return True, result.stdout
        else:
            console.print(f"[red]✗[/red] {description} failed")
            if result.stdout:
                console.print(result.stdout)
            if result.stderr:
                console.print(f"[red]{result.stderr}[/red]")
            if stop_on_error:
                console.print(f"\n[red]Stopping on first error (--stop-on-error)[/red]")
                sys.exit(1)
            return False, result.stderr

    except subprocess.TimeoutExpired:
        console.print(f"[red]✗[/red] {description} timed out")
        return False, "Timeout"
    except Exception as e:
        console.print(f"[red]✗[/red] {description} error: {e}")
        return False, str(e)


def main() -> int:
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Run all code quality checks")
    parser.add_argument(
        "--stop-on-error",
        action="store_true",
        help="Stop on first error",
    )
    parser.add_argument(
        "--skip-tests",
        action="store_true",
        help="Skip running tests",
    )

    args = parser.parse_args()

    console.print(Panel.fit("[bold blue]Code Quality Checks[/bold blue]", border_style="blue"))

    results: list[tuple[str, bool]] = []

    ruff_check_cmd = find_command("ruff")
    if ruff_check_cmd:
        success, _ = run_command(
            f"{ruff_check_cmd} check .",
            "Ruff linting",
            args.stop_on_error,
        )
        results.append(("Ruff linting", success))
    else:
        console.print("[yellow]⚠[/yellow] ruff not found, skipping")
        results.append(("Ruff linting", False))

    ruff_format_cmd = find_command("ruff")
    if ruff_format_cmd:
        success, _ = run_command(
            f"{ruff_format_cmd} format --check .",
            "Ruff formatting check",
            args.stop_on_error,
        )
        results.append(("Ruff formatting", success))
    else:
        console.print("[yellow]⚠[/yellow] ruff not found, skipping")
        results.append(("Ruff formatting", False))

    mypy_cmd = find_command("mypy")
    if mypy_cmd:
        success, _ = run_command(
            f"{mypy_cmd} .",
            "MyPy type checking",
            args.stop_on_error,
        )
        results.append(("MyPy type checking", success))
    else:
        console.print("[yellow]⚠[/yellow] mypy not found, skipping")
        results.append(("MyPy type checking", False))

    if not args.skip_tests:
        pytest_cmd = find_command("pytest")
        if pytest_cmd:
            success, _ = run_command(
                f"{pytest_cmd}",
                "Pytest tests",
                args.stop_on_error,
            )
            results.append(("Pytest tests", success))
        else:
            console.print("[yellow]⚠[/yellow] pytest not found, skipping")
            results.append(("Pytest tests", False))
    else:
        console.print("[yellow]⚠[/yellow] Skipping tests (--skip-tests)")
        results.append(("Pytest tests", None))

    console.print()

    table = Table(title="Summary", show_header=True, header_style="bold magenta")
    table.add_column("Check", style="cyan")
    table.add_column("Status", style="bold")

    all_passed = True
    for check_name, success in results:
        if success is None:
            status = "[yellow]Skipped[/yellow]"
        elif success:
            status = "[green]✓ Passed[/green]"
        else:
            status = "[red]✗ Failed[/red]"
            all_passed = False
        table.add_row(check_name, status)

    console.print(table)

    if all_passed:
        console.print(Panel.fit("[bold green]All checks passed![/bold green]", border_style="green"))
        return 0

    console.print(Panel.fit("[bold red]Some checks failed[/bold red]", border_style="red"))
    return 1


if __name__ == "__main__":
    sys.exit(main())
