# Trading Research Assistant

LLM-powered trading research assistant for technical and fundamental analysis.

## Installation

### Using uv (recommended)

```bash
# Base dependencies (required)
uv sync

# With LLM support
uv sync --extra llm

# With UI support
uv sync --extra ui

# With all optional dependencies
uv sync --all-extras

# With dev dependencies
uv sync --extra dev
```

### Using pip

```bash
# Base dependencies
pip install -e .

# With optional groups
pip install -e ".[llm,ui,dev]"
```

## Dependency Groups

- **Base** (required): `pydantic`, `pydantic-settings`, `httpx`, `tenacity`, `numpy`, `pandas`, `ta`
- **llm** (optional): `ollama` - for LLM integration
- **ui** (optional): `rich` - for CLI dashboard
- **dev** (optional): `pytest`, `ruff`, `mypy`, `pre-commit` - for development

## Architecture

See [docs/ru/import_rules.md](docs/ru/import_rules.md) for import rules and dependency graph.
