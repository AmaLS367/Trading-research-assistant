#!/bin/bash
# Backup and restore SQLite database

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

cd "$PROJECT_ROOT"

if command -v uv &> /dev/null; then
    uv run python scripts/python/backup_database.py "$@"
else
    python scripts/python/backup_database.py "$@"
fi
