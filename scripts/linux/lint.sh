#!/bin/bash
# Run linting and type checking

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

cd "$PROJECT_ROOT"

if command -v uv &> /dev/null; then
    echo "Running ruff check..."
    uv run ruff check .
    echo "Running mypy..."
    uv run mypy .
else
    echo "Running ruff check..."
    ruff check .
    echo "Running mypy..."
    mypy .
fi

echo "All checks passed!"
