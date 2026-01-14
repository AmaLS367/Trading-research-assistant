# Utility Scripts

This directory contains utility scripts for development, setup, maintenance, and analysis tasks.

## Structure

- `python/` - Cross-platform Python scripts (work on Linux, Windows, macOS)
- `linux/` - Bash wrapper scripts for Linux/macOS
- `windows/` - PowerShell wrapper scripts for Windows

## Python Scripts

All Python scripts are located in `scripts/python/` and can be run directly:

```bash
# Using uv (recommended)
uv run python scripts/python/check_environment.py

# Using python directly
python scripts/python/check_environment.py
```

### Available Scripts

#### `check_environment.py`

Check project environment and dependencies:

- Python version (>= 3.11)
- `uv` availability
- Ollama server accessibility
- `.env` file existence
- Required environment variables
- Database file existence

```bash
python scripts/python/check_environment.py
```

#### `setup_environment.py`

Interactive helper for setting up `.env` file:

- Checks for existing `.env` file
- Step-by-step variable input with hints
- Validates entered values
- Creates `.env.example` if missing
- Supports non-interactive mode for CI/CD

```bash
# Interactive mode
python scripts/python/setup_environment.py

# Non-interactive mode (creates .env.example only)
python scripts/python/setup_environment.py --non-interactive
```

#### `clean_cache.py`

Clean temporary files and caches:

- `__pycache__` directories
- `.pytest_cache`, `.mypy_cache`, `.ruff_cache`
- `.coverage` files
- `*.pyc` files
- Optional: `artifacts/`, `dist/`, `build/`

```bash
# Interactive (with confirmation)
python scripts/python/clean_cache.py

# Clean everything including artifacts
python scripts/python/clean_cache.py --all

# Skip confirmation
python scripts/python/clean_cache.py --yes
```

#### `backup_database.py`

Backup and restore SQLite database:

- Create timestamped backups
- Optional gzip compression
- List available backups
- Restore from backup
- Cleanup old backups

```bash
# Create backup
python scripts/python/backup_database.py

# Create compressed backup
python scripts/python/backup_database.py --compress

# List backups
python scripts/python/backup_database.py --list

# Restore from latest backup
python scripts/python/backup_database.py --restore latest

# Restore from specific backup
python scripts/python/backup_database.py --restore backups/forex_research_assistant_20240101_120000.db

# Keep only 10 most recent backups
python scripts/python/backup_database.py --cleanup 10
```

#### `run_all_checks.py`

Run all code quality checks:

- `ruff check` (linting)
- `ruff format --check` (formatting)
- `mypy` (type checking)
- `pytest` (tests)
- Summary report

```bash
# Run all checks
python scripts/python/run_all_checks.py

# Stop on first error
python scripts/python/run_all_checks.py --stop-on-error

# Skip tests
python scripts/python/run_all_checks.py --skip-tests
```

#### `initialize_project.py`

Full project initialization:

- Check environment
- Install dependencies via `uv`
- Create `.env` if missing
- Initialize database
- Verify setup

```bash
# Full initialization
python scripts/python/initialize_project.py

# Skip dependency installation
python scripts/python/initialize_project.py --skip-deps

# Skip .env setup
python scripts/python/initialize_project.py --skip-env

# Skip database initialization
python scripts/python/initialize_project.py --skip-db
```

## Linux/macOS Wrapper Scripts

Bash scripts in `scripts/linux/` provide convenient shortcuts:

```bash
# Make scripts executable (first time only)
chmod +x scripts/linux/*.sh

# Run scripts
./scripts/linux/setup.sh
./scripts/linux/check.sh
./scripts/linux/clean.sh
./scripts/linux/backup.sh
./scripts/linux/test.sh
./scripts/linux/lint.sh
./scripts/linux/format.sh
./scripts/linux/run_checks.sh
```

All scripts automatically:
- Detect project root
- Use `uv run` if available, otherwise `python`
- Handle errors gracefully

## Windows Wrapper Scripts

PowerShell scripts in `scripts/windows/` provide convenient shortcuts:

```powershell
# Run scripts
.\scripts\windows\setup.ps1
.\scripts\windows\check.ps1
.\scripts\windows\clean.ps1
.\scripts\windows\backup.ps1
.\scripts\windows\test.ps1
.\scripts\windows\lint.ps1
.\scripts\windows\format.ps1
.\scripts\windows\run_checks.ps1
```

All scripts automatically:
- Detect project root
- Use `uv run` if available, otherwise `python`
- Handle errors with `$ErrorActionPreference = "Stop"`

## Quick Start

### First Time Setup

```bash
# Linux/macOS
./scripts/linux/setup.sh

# Windows
.\scripts\windows\setup.ps1

# Or using Python directly
python scripts/python/initialize_project.py
```

### Daily Development

```bash
# Check environment
./scripts/linux/check.sh  # or .\scripts\windows\check.ps1

# Run tests
./scripts/linux/test.sh  # or .\scripts\windows\test.ps1

# Run all checks
./scripts/linux/run_checks.sh  # or .\scripts\windows\run_checks.ps1

# Clean cache
./scripts/linux/clean.sh  # or .\scripts\windows\clean.ps1
```

### Maintenance

```bash
# Backup database
./scripts/linux/backup.sh --compress  # or .\scripts\windows\backup.ps1 --compress

# List backups
./scripts/linux/backup.sh --list  # or .\scripts\windows\backup.ps1 --list

# Restore from backup
./scripts/linux/backup.sh --restore latest  # or .\scripts\windows\backup.ps1 --restore latest
```

## Notes

- All Python scripts use `rich` for beautiful colored output
- Scripts follow project coding standards (typing, style)
- Error handling with clear messages
- All scripts support `--help` flag
- Cross-platform compatibility (Windows paths, encodings)
