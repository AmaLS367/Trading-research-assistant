#!/usr/bin/env python3
"""
Architecture boundary checker for Trading Research Assistant.

Validates that import rules are followed:
- src/runtime/** does not import src/app/**
- src/llm/** does not import src/app/**
- src/core/** does not import src/app/**

This is a text-based analysis without AST parsing for simplicity.
"""

import re
import sys
from pathlib import Path

# Define forbidden import patterns
FORBIDDEN_IMPORTS = [
    # (source_pattern, forbidden_import_pattern, description)
    (r"src/runtime/.*\.py$", r"from src\.app\.(settings|main|wiring)", "runtime -> app"),
    (r"src/llm/.*\.py$", r"from src\.app\.(settings|main|wiring)", "llm -> app"),
    (r"src/core/.*\.py$", r"from src\.app\.(settings|main|wiring)", "core -> app"),
]

# Allowlist for TYPE_CHECKING imports (these are OK because they only run at type-check time)
TYPE_CHECKING_ALLOWLIST = [
    # (file_pattern, import_pattern)
    (r"src/runtime/preflight\.py$", r"from src\.app\.settings import Settings"),
]


def is_in_type_checking_block(lines: list[str], import_line_idx: int) -> bool:
    """Check if the import is inside a TYPE_CHECKING block."""
    in_type_checking = False
    indent_level = 0

    for i, line in enumerate(lines):
        stripped = line.strip()

        # Detect TYPE_CHECKING block
        if "if TYPE_CHECKING:" in stripped:
            in_type_checking = True
            indent_level = len(line) - len(line.lstrip())
            continue

        if in_type_checking:
            # Check if we're still in the block
            current_indent = len(line) - len(line.lstrip()) if line.strip() else indent_level + 1
            if line.strip() and current_indent <= indent_level and not stripped.startswith("#"):
                in_type_checking = False

        if i == import_line_idx:
            return in_type_checking

    return False


def is_allowlisted(file_path: str, import_line: str) -> bool:
    """Check if the import is in the allowlist."""
    for file_pattern, import_pattern in TYPE_CHECKING_ALLOWLIST:
        if re.search(file_pattern, file_path) and re.search(import_pattern, import_line):
            return True
    return False


def check_file(file_path: Path, project_root: Path) -> list[str]:
    """Check a single file for forbidden imports."""
    violations = []
    relative_path = str(file_path.relative_to(project_root))

    try:
        content = file_path.read_text(encoding="utf-8")
        lines = content.split("\n")
    except UnicodeDecodeError:
        return []

    for source_pattern, forbidden_pattern, description in FORBIDDEN_IMPORTS:
        if not re.search(source_pattern, relative_path):
            continue

        for line_num, line in enumerate(lines):
            stripped = line.strip()

            # Skip comments and docstrings
            if stripped.startswith("#") or stripped.startswith('"""') or stripped.startswith("'''"):
                continue

            # Only check actual import statements
            if not (stripped.startswith("from ") or stripped.startswith("import ")):
                continue

            if re.search(forbidden_pattern, line):
                # Check if in TYPE_CHECKING block
                if is_in_type_checking_block(lines, line_num):
                    continue

                # Check allowlist
                if is_allowlisted(relative_path, line):
                    continue

                violations.append(
                    f"{relative_path}:{line_num + 1}: {description}\n    {line.strip()}"
                )

    return violations


def main() -> int:
    """Run the import boundary checker."""
    project_root = Path(__file__).parent.parent.parent
    src_dir = project_root / "src"

    if not src_dir.exists():
        print(f"Error: src directory not found at {src_dir}")
        return 1

    all_violations: list[str] = []

    for py_file in src_dir.rglob("*.py"):
        violations = check_file(py_file, project_root)
        all_violations.extend(violations)

    if all_violations:
        print("Import boundary violations found:")
        print()
        for violation in all_violations:
            print(violation)
            print()
        return 1
    else:
        print("No import boundary violations found.")
        return 0


if __name__ == "__main__":
    sys.exit(main())
