"""Clean temporary files and caches."""
import shutil
import sys
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm

console = Console()

EXCLUDE_DIRS = {".venv", "venv", "env", ".git", "node_modules", ".idea", ".vscode"}

CACHE_PATTERNS = [
    ("__pycache__", "directories"),
    (".pytest_cache", "directories"),
    (".mypy_cache", "directories"),
    (".ruff_cache", "directories"),
    ("*.pyc", "files"),
    (".coverage", "files"),
    ("htmlcov", "directories"),
]

OPTIONAL_CLEANUP = [
    ("artifacts", "directories"),
    ("dist", "directories"),
    ("build", "directories"),
    ("*.egg-info", "directories"),
]


def should_exclude_path(path: Path) -> bool:
    """Check if path should be excluded from cleanup."""
    parts = path.parts
    for exclude_dir in EXCLUDE_DIRS:
        if exclude_dir in parts:
            return True
    return False


def find_cache_items(pattern: str, item_type: str) -> list[Path]:
    """Find cache items matching pattern."""
    items: list[Path] = []
    root = Path(".")

    if item_type == "directories":
        if pattern == "__pycache__":
            for path in root.rglob(pattern):
                if path.is_dir() and not should_exclude_path(path):
                    items.append(path)
        elif pattern.endswith("*"):
            for path in root.glob(pattern):
                if path.is_dir() and not should_exclude_path(path):
                    items.append(path)
        else:
            path = root / pattern
            if path.exists() and path.is_dir() and not should_exclude_path(path):
                items.append(path)
    else:
        for path in root.rglob(pattern):
            if path.is_file() and not should_exclude_path(path):
                items.append(path)

    return items


def remove_items(items: list[Path], item_type: str) -> int:
    """Remove cache items."""
    removed_count = 0
    for item in items:
        try:
            if item_type == "directories":
                shutil.rmtree(item)
            else:
                item.unlink()
            removed_count += 1
        except Exception as e:
            console.print(f"[yellow]⚠[/yellow] Failed to remove {item}: {e}")
    return removed_count


def clean_cache(include_optional: bool = False) -> None:
    """Clean all cache files and directories."""
    console.print(Panel.fit("[bold blue]Cache Cleanup[/bold blue]", border_style="blue"))

    all_items: list[tuple[Path, str]] = []

    for pattern, item_type in CACHE_PATTERNS:
        items = find_cache_items(pattern, item_type)
        for item in items:
            all_items.append((item, item_type))

    if include_optional:
        for pattern, item_type in OPTIONAL_CLEANUP:
            items = find_cache_items(pattern, item_type)
            for item in items:
                all_items.append((item, item_type))

    if not all_items:
        console.print("[green]✓[/green] No cache files found to clean")
        return

    console.print(f"\nFound {len(all_items)} item(s) to remove:")
    for item, _ in all_items[:10]:
        console.print(f"  - {item}")
    if len(all_items) > 10:
        console.print(f"  ... and {len(all_items) - 10} more")

    if not Confirm.ask("\nProceed with cleanup?", default=True):
        console.print("[yellow]Cleanup cancelled.[/yellow]")
        return

    removed_dirs = 0
    removed_files = 0
    failed_count = 0

    for item, item_type in all_items:
        if not item.exists():
            continue

        try:
            if item_type == "directories":
                shutil.rmtree(item)
                removed_dirs += 1
            else:
                item.unlink()
                removed_files += 1
        except FileNotFoundError:
            pass
        except PermissionError as e:
            console.print(f"[yellow]⚠[/yellow] Permission denied: {item}")
            failed_count += 1
        except Exception as e:
            console.print(f"[yellow]⚠[/yellow] Failed to remove {item}: {e}")
            failed_count += 1

    if failed_count > 0:
        console.print(f"\n[yellow]⚠[/yellow] {failed_count} item(s) could not be removed")
    console.print(f"\n[green]✓[/green] Removed {removed_dirs} directory(ies) and {removed_files} file(s)")


def main() -> int:
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Clean temporary files and caches")
    parser.add_argument(
        "--all",
        action="store_true",
        help="Also clean artifacts, dist, build directories",
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Skip confirmation prompt",
    )

    args = parser.parse_args()

    if args.yes:
        console.print("[yellow]Skipping confirmation (--yes flag)[/yellow]")

    try:
        if args.yes:
            all_items: list[tuple[Path, str]] = []
            for pattern, item_type in CACHE_PATTERNS:
                items = find_cache_items(pattern, item_type)
                for item in items:
                    all_items.append((item, item_type))

            if args.all:
                for pattern, item_type in OPTIONAL_CLEANUP:
                    items = find_cache_items(pattern, item_type)
                    for item in items:
                        all_items.append((item, item_type))

            removed_dirs = 0
            removed_files = 0
            failed_count = 0

            for item, item_type in all_items:
                if not item.exists():
                    continue

                try:
                    if item_type == "directories":
                        shutil.rmtree(item)
                        removed_dirs += 1
                    else:
                        item.unlink()
                        removed_files += 1
                except FileNotFoundError:
                    pass
                except PermissionError:
                    console.print(f"[yellow]⚠[/yellow] Permission denied: {item}")
                    failed_count += 1
                except Exception as e:
                    console.print(f"[yellow]⚠[/yellow] Failed to remove {item}: {e}")
                    failed_count += 1

            if failed_count > 0:
                console.print(f"[yellow]⚠[/yellow] {failed_count} item(s) could not be removed")
            console.print(f"[green]✓[/green] Removed {removed_dirs} directory(ies) and {removed_files} file(s)")
        else:
            clean_cache(include_optional=args.all)
        return 0
    except KeyboardInterrupt:
        console.print("\n[yellow]Cleanup cancelled by user.[/yellow]")
        return 1
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        return 1


if __name__ == "__main__":
    sys.exit(main())
