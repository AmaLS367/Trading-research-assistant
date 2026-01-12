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

## Quick Start

### Prerequisites

1. Python 3.11 or higher
2. Ollama installed and running (for LLM features)
3. OANDA API key (for market data)

### Setup

1. **Install dependencies:**
   ```bash
   uv sync --extra dev
   ```

2. **Configure environment variables:**
   Create a `.env` file or set the following:
   ```bash
   OANDA_API_KEY=your_oanda_api_key
   OANDA_BASE_URL=https://api-fxpractice.oanda.com
   OLLAMA_BASE_URL=http://localhost:11434
   OLLAMA_MODEL=your_model_name
   STORAGE_SQLITE_DB_PATH=db/forex_research_assistant.sqlite3
   ```

3. **Initialize database:**
   ```bash
   python src/app/main.py init-db
   ```

4. **Run analysis:**
   ```bash
   python src/app/main.py analyze --symbol EURUSD --timeframe 1h
   ```

5. **View latest recommendation:**
   ```bash
   python src/app/main.py show-latest
   ```

## Usage

### Commands

- `init-db` - Initialize database and run migrations
- `analyze --symbol SYMBOL [--timeframe TIMEFRAME]` - Run full analysis pipeline
  - Example: `analyze --symbol EURUSD --timeframe 1h`
  - Supported timeframes: `1m`, `5m`, `15m`, `1h`, `1d`
- `show-latest` - Display the latest recommendation with color-coded action and confidence
- `log-open --symbol SYMBOL --action CALL|PUT [--expiry SECONDS]` - Log a trade opening
- `log-outcome --result WIN|LOSS|DRAW [--comment TEXT]` - Log trade outcome

## Architecture

See [docs/ru/import_rules.md](docs/ru/import_rules.md) for import rules and dependency graph.
