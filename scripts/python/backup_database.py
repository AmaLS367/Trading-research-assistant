"""Backup and restore SQLite database."""

import gzip
import shutil
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm

console = Console()


def get_backup_path(compress: bool = False) -> Path:
    """Generate backup file path with timestamp."""
    backup_dir = Path("backups")
    backup_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    extension = ".db.gz" if compress else ".db"
    backup_path = backup_dir / f"forex_research_assistant_{timestamp}{extension}"

    return backup_path


def backup_database(compress: bool = False) -> Path | None:
    """Create a backup of the database."""
    try:
        from src.app.settings import settings

        db_path = Path(settings.storage_sqlite_db_path)
        if not db_path.exists():
            console.print(f"[red]✗[/red] Database file not found at {db_path}")
            return None

        backup_path = get_backup_path(compress)

        if compress:
            with open(db_path, "rb") as src, gzip.open(backup_path, "wb") as dst:
                shutil.copyfileobj(src, dst)
            console.print(f"[green]✓[/green] Database backed up (compressed) to {backup_path}")
        else:
            shutil.copy2(db_path, backup_path)
            console.print(f"[green]✓[/green] Database backed up to {backup_path}")

        file_size = backup_path.stat().st_size
        size_mb = file_size / (1024 * 1024)
        console.print(f"  Size: {size_mb:.2f} MB")

        return backup_path
    except ImportError:
        console.print("[red]✗[/red] Cannot import settings")
        return None
    except Exception as e:
        console.print(f"[red]✗[/red] Error creating backup: {e}")
        return None


def list_backups() -> list[Path]:
    """List all available backups."""
    backup_dir = Path("backups")
    if not backup_dir.exists():
        return []

    backups: list[Path] = []
    for path in backup_dir.iterdir():
        if path.is_file() and (path.name.endswith(".db") or path.name.endswith(".db.gz")):
            backups.append(path)

    return sorted(backups, reverse=True)


def restore_database(backup_path: Path, compress: bool = False) -> bool:
    """Restore database from backup."""
    try:
        from src.app.settings import settings

        db_path = Path(settings.storage_sqlite_db_path)

        if not backup_path.exists():
            console.print(f"[red]✗[/red] Backup file not found: {backup_path}")
            return False

        if db_path.exists():
            if not Confirm.ask(f"Database file exists at {db_path}. Overwrite?", default=False):
                console.print("[yellow]Restore cancelled.[/yellow]")
                return False

        if compress or backup_path.suffix == ".gz":
            with gzip.open(backup_path, "rb") as src, open(db_path, "wb") as dst:
                shutil.copyfileobj(src, dst)
        else:
            shutil.copy2(backup_path, db_path)

        console.print(f"[green]✓[/green] Database restored from {backup_path}")
        return True
    except ImportError:
        console.print("[red]✗[/red] Cannot import settings")
        return False
    except Exception as e:
        console.print(f"[red]✗[/red] Error restoring backup: {e}")
        return False


def cleanup_old_backups(keep_count: int = 10) -> int:
    """Remove old backups, keeping only the most recent ones."""
    backups = list_backups()
    if len(backups) <= keep_count:
        return 0

    to_remove = backups[keep_count:]
    removed_count = 0

    for backup in to_remove:
        try:
            backup.unlink()
            removed_count += 1
        except Exception as e:
            console.print(f"[yellow]⚠[/yellow] Failed to remove {backup}: {e}")

    return removed_count


def main() -> int:
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Backup and restore SQLite database")
    parser.add_argument(
        "--compress",
        action="store_true",
        help="Compress backup with gzip",
    )
    parser.add_argument(
        "--restore",
        type=str,
        help="Restore from backup file (path or 'latest')",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List all available backups",
    )
    parser.add_argument(
        "--cleanup",
        type=int,
        metavar="N",
        help="Remove old backups, keeping only N most recent",
    )

    args = parser.parse_args()

    try:
        if args.list:
            backups = list_backups()
            if not backups:
                console.print("[yellow]No backups found.[/yellow]")
                return 0

            console.print(
                Panel.fit("[bold blue]Available Backups[/bold blue]", border_style="blue")
            )
            for i, backup in enumerate(backups, 1):
                size = backup.stat().st_size / (1024 * 1024)
                mtime = datetime.fromtimestamp(backup.stat().st_mtime)
                console.print(
                    f"{i}. {backup.name} ({size:.2f} MB, {mtime.strftime('%Y-%m-%d %H:%M:%S')})"
                )
            return 0

        if args.restore:
            if args.restore == "latest":
                backups = list_backups()
                if not backups:
                    console.print("[red]✗[/red] No backups found")
                    return 1
                backup_path = backups[0]
                console.print(f"Restoring from latest backup: {backup_path.name}")
            else:
                backup_path = Path(args.restore)

            compress = backup_path.suffix == ".gz"
            if restore_database(backup_path, compress):
                return 0
            return 1

        if args.cleanup is not None:
            removed = cleanup_old_backups(args.cleanup)
            console.print(f"[green]✓[/green] Removed {removed} old backup(s)")
            return 0

        console.print(Panel.fit("[bold blue]Database Backup[/bold blue]", border_style="blue"))
        backup_path = backup_database(compress=args.compress)
        if backup_path:
            return 0
        return 1

    except KeyboardInterrupt:
        console.print("\n[yellow]Operation cancelled by user.[/yellow]")
        return 1
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        return 1


if __name__ == "__main__":
    sys.exit(main())
