#!/bin/bash
# Initialize project: check environment, install dependencies, setup .env, init DB

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

cd "$PROJECT_ROOT"

if command -v uv &> /dev/null; then
    uv run python scripts/python/initialize_project.py "$@"
else
    python scripts/python/initialize_project.py "$@"
fi
