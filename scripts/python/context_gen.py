import os

IGNORE_DIRS = {
    ".git",
    "__pycache__",
    ".venv",
    "venv",
    "env",
    ".idea",
    ".vscode",
    "logs",
    "artifacts",
    "reports",
    "data",
    "build",
    "dist",
    "node_modules",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    # "docs", # Documentation files (docs/) are excluded from context generation
}
INCLUDE_EXT = {
    ".py",
    ".toml",
    ".md",
    ".yml",
    ".yaml",
    ".Dockerfile",
    ".ts",
    ".tsx",
    ".json",
    ".sql",
}
IGNORE_FILES = {
    "poetry.lock",
    "yarn.lock",
    "package-lock.json",
    "trading_research_assistant_context.txt",  # Exclude the output file itself
    ".cursorrules",
    # "README.md",
    # "CONTRIBUTING.md",
    # "CODE_OF_CONDUCT.md",
    # "LICENSE",
}
IGNORE_EXT = {".db", ".sqlite", ".sqlite3"}


def generate_context() -> None:
    output_file = "trading_research_assistant_context.txt"

    with open(output_file, "w", encoding="utf-8") as outfile:
        outfile.write("# Trading Research Assistant - Project Context\n")
        outfile.write("# Generated automatically. Documentation files (docs/) are excluded.\n\n")

        for root, dirs, files in os.walk("."):
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRS and not d.endswith(".egg-info")]

            for file in files:
                if file in IGNORE_FILES:
                    continue

                _, ext = os.path.splitext(file)
                if ext in IGNORE_EXT:
                    continue

                if ext in INCLUDE_EXT or file == "Dockerfile":
                    path = os.path.join(root, file)

                    outfile.write(f"\n{'=' * 20}\nFILE: {path}\n{'=' * 20}\n")

                    try:
                        with open(path, encoding="utf-8") as infile:
                            outfile.write(infile.read())
                    except Exception as e:
                        outfile.write(f"Error reading file: {e}")

    print(f"Ready. File {output_file} created.")


if __name__ == "__main__":
    generate_context()
