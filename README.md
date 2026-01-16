<div align="center">

# Trading Research Assistant

**LLM-powered trading research assistant for technical and fundamental analysis**

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![uv](https://img.shields.io/badge/uv-Latest-FFD43B?logo=python&logoColor=black)](https://github.com/astral-sh/uv)
[![SQLite](https://img.shields.io/badge/SQLite-3-003B57?logo=sqlite&logoColor=white)](https://www.sqlite.org/)
[![Ollama](https://img.shields.io/badge/Ollama-Local%20LLM-FF6B6B?logo=ollama)](https://ollama.ai/)
[![Rich](https://img.shields.io/badge/Rich-CLI-FFD43B?logo=python&logoColor=black)](https://rich.readthedocs.io/)

</div>

---

<div align="center">

### Features

**Technical Analysis** • **Fundamental Analysis** • **LLM-Powered Insights** • **Trade Journal** • **Automated Reports**

</div>

---

## About

Trading Research Assistant is a production-ready automated financial market analysis system that uses Large Language Models (LLM) to generate trading recommendations based on technical and fundamental analysis. Built with clean architecture principles and designed for extensibility.

⚠️ **Demo Only**: This system is for research and analysis purposes only. All recommendations require manual execution. Not financial advice.

### Key Features

- 📊 **Technical Analysis** - Automatic indicator calculation and chart analysis via LLM
- 📰 **Fundamental Analysis** - News aggregation and analysis from various sources (GDELT, NewsAPI)
- 🤖 **LLM Agents** - Use of local or remote LLM models (Ollama) for analysis
- 💾 **Trade Journal** - Track trading results and statistics
- 📈 **Reports** - Generate trading operation statistics
- 🔄 **Fallback Providers** - Automatic switching between data sources (OANDA, Twelve Data)
- 🏗️ **Clean Architecture** - Domain-driven design with ports & adapters pattern
- 🧪 **Testable** - Each layer can be tested independently

---

## Quick Start

### Requirements

- Python 3.11 or higher
- uv (recommended) or pip
- Ollama installed and running (for LLM features)
- API keys for data providers (OANDA, Twelve Data)

### Installation

#### Using uv (recommended)

```bash
# Base dependencies (required)
uv sync

# With dev dependencies (testing, linting)
uv sync --extra dev
```

#### Using pip

```bash
# Base dependencies
pip install -e .

# With dev dependencies
pip install -e ".[dev]"
```

### Setup

1. **Install dependencies:**
   ```bash
   uv sync --extra dev
   ```

2. **Configure environment variables:**
   Copy `.env.example` to `.env` and fill in your API keys:
   
   **Windows (PowerShell):**
   ```powershell
   Copy-Item .env.example .env
   ```
   
   **Linux/macOS:**
   ```bash
   cp .env.example .env
   ```
   
   Then edit `.env` and replace placeholder values with your actual API keys.

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

---

## Usage

### Commands

- `init-db` - Initialize database and run migrations
- `analyze --symbol SYMBOL [--timeframe TIMEFRAME] [--verbose]` - Run full analysis pipeline
  - Example: `analyze --symbol EURUSD --timeframe 1h`
  - Supported timeframes: `1m`, `5m`, `15m`, `1h`, `1d`
  - Use `--verbose` to show detailed analysis output during execution
- `show-latest [--details]` - Display the latest recommendation with color-coded action and confidence
  - Use `--details` to show full rationales (technical analysis, news context, synthesis)
- `journal` - Interactive command for logging trading decisions
- `report` - View trading statistics and reports

---

## Dependency Groups

- **Base** (required): `pydantic`, `pydantic-settings`, `httpx`, `tenacity`, `numpy`, `pandas`, `ta`, `ollama`, `rich`
- **dev** (optional): `pytest`, `ruff`, `mypy` - for development and testing

---

## Documentation

Comprehensive documentation is available in the [`docs/`](./docs/) directory:

**English:**

- 📖 [Overview](./docs/en/overview.md) - Project overview and key features
- 🏗️ [Architecture](./docs/en/architecture.md) - Project structure and design patterns
- 📚 [Usage Guide](./docs/en/usage_guide.md) - Installation and usage instructions
- ⚙️ [Environment Configuration](./docs/en/env_configuration.md) - Complete description of all .env variables
- 🤖 [LLM Task Routing](./docs/en/llm_task_routing.md) - LLM routing by tasks and branches
- 🔧 [Troubleshooting](./docs/en/troubleshooting.md) - Common issues and solutions
- 🔒 [Safety Policy](./docs/en/safety_policy.md) - Safety policy and risk management
- 📋 [Import Rules](./docs/en/import_rules.md) - Import rules and dependency graph

**Русский:**

- 📖 [Обзор](./docs/ru/overview.md) - Обзор проекта и основные возможности
- 🏗️ [Архитектура](./docs/ru/architecture.md) - Структура проекта и паттерны проектирования
- 📚 [Руководство по использованию](./docs/ru/usage_guide.md) - Инструкции по установке и использованию
- ⚙️ [Конфигурация переменных окружения](./docs/ru/env_configuration.md) - Полное описание всех переменных .env
- 🤖 [LLM Task Routing](./docs/ru/llm_task_routing.md) - Маршрутизация LLM по задачам и веткам
- 🔧 [Устранение неполадок](./docs/ru/troubleshooting.md) - Распространенные проблемы и решения
- 🔒 [Политика безопасности](./docs/ru/safety_policy.md) - Политика безопасности и управление рисками
- 📋 [Правила импортов](./docs/ru/import_rules.md) - Правила импортов и граф зависимостей

---

## Tech Stack

<div align="center">

| Category             | Technology                     |
| -------------------- | ------------------------------ |
| **Language**         | Python 3.11+                   |
| **Package Manager**  | uv                             |
| **Data Validation**  | Pydantic 2.0+                  |
| **HTTP Client**      | httpx 0.25+                     |
| **Retry Logic**      | tenacity 8.2+                  |
| **Data Processing**  | pandas 2.0+, numpy 1.24+       |
| **Technical Analysis** | ta 0.11+                      |
| **LLM Provider**     | Ollama (local or remote)        |
| **CLI Interface**    | Rich 13.0+                      |
| **Database**         | SQLite 3                        |
| **Testing**          | pytest 7.4+                     |
| **Linting**          | ruff 0.1+                       |
| **Type Checking**    | mypy 1.5+                       |

</div>

---

## Project Structure

```
Trading-research-assistant/
├── src/
│   ├── core/              # Domain logic (models, ports, services, policies)
│   ├── data_providers/    # Market data adapters (OANDA, Twelve Data)
│   ├── news_providers/    # News adapters (GDELT, NewsAPI)
│   ├── features/          # Technical indicators, volatility, regime detection
│   ├── agents/            # LLM agents for analysis
│   ├── llm/               # LLM providers (Ollama)
│   ├── storage/           # SQLite repositories and artifact store
│   ├── runtime/           # Orchestration and jobs
│   ├── ui/                # CLI interface (Rich)
│   ├── app/               # Entry point and settings
│   ├── broker_journal/    # Trade journal management
│   └── utils/             # Utilities (logging, retry, time)
├── tests/                 # Unit and integration tests
├── docs/                  # Documentation (en/ru)
│   ├── en/               # English documentation
│   └── ru/               # Russian documentation
├── scripts/              # Utility scripts
├── db/                   # SQLite database directory
└── pyproject.toml        # Project configuration
```

For detailed structure, see [Architecture Documentation](./docs/en/architecture.md).

---

## Architecture

The project is built on **Clean Architecture** principles using the **Ports & Adapters** pattern. The system core (`core`) is completely isolated from external dependencies and only knows about business logic.

**Key Rule**: `core` does not know about external integrations. External modules implement interfaces from `core/ports`.

**Dependency Graph:**
```
app → runtime → (features, agents, storage, providers, llm) → core
```

For detailed architecture documentation, see:
- [Architecture (English)](./docs/en/architecture.md)
- [Architecture (Русский)](./docs/ru/architecture.md)
- [Import Rules (English)](./docs/en/import_rules.md)
- [Import Rules (Русский)](./docs/ru/import_rules.md)

---

## Supported Providers

### Market Data
- **OANDA** — primary provider for Forex
- **Twelve Data** — fallback provider

### News
- **GDELT** — global news database
- **NewsAPI** — news aggregator

### LLM
- **Multi-provider routing** — Support for Ollama (local/server) and DeepSeek API
- **Task-based routing** — Configure different models for different tasks (tech analysis, news analysis, synthesis, verification)
- **Automatic fallback** — Falls back to available providers if primary fails
- **Health checks** — Provider availability checking with caching
- **Verification stage** — Optional LLM-based verification of agent outputs
- **Legacy support** — Backward compatible with `OLLAMA_BASE_URL` and `OLLAMA_MODEL` during transition

---

## Safety Policy

The system includes a safety policy that validates recommendations before issuing them. See [Safety Policy Documentation](./docs/en/safety_policy.md) for details.

⚠️ **Important**: Trading Research Assistant is a research and analysis tool, not an automated trading system. The system does not guarantee recommendation profitability. All trading decisions are made by the user independently.

---

## Acknowledgments

- [Ollama](https://ollama.ai/) for local LLM capabilities
- [Rich](https://rich.readthedocs.io/) for beautiful CLI interface
- [Pydantic](https://docs.pydantic.dev/) for data validation
- [uv](https://github.com/astral-sh/uv) for fast Python package management
- [OANDA](https://www.oanda.com/) and [Twelve Data](https://twelvedata.com/) for market data APIs
- [GDELT](https://www.gdeltproject.org/) for news data

---

<div align="center">

**Made with ❤️ using Python, Clean Architecture, and LLM**

[📖 Documentation](./docs/) • [🏗️ Architecture](./docs/en/architecture.md) • [📚 Usage Guide](./docs/en/usage_guide.md)

</div>
