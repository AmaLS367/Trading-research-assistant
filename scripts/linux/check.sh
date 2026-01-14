#!/bin/bash
# Check project environment and dependencies

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

cd "$PROJECT_ROOT"

if command -v uv &> /dev/null; then
    uv run python scripts/python/check_environment.py "$@"
else
    python scripts/python/check_environment.py "$@"
fi
