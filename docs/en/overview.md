# Project Overview

## What is this?

**Trading Research Assistant** is an automated financial market analysis system that uses LLM (Large Language Models) to generate trading recommendations based on technical and fundamental analysis.

## Key Features

- 📊 **Technical Analysis**: Automatic indicator calculation and chart analysis via LLM
- 📰 **Fundamental Analysis**: News aggregation and analysis from various sources
- 🤖 **LLM Agents**: Use of local or remote LLM models for analysis
- 💾 **Trade Journal**: Track trading results and statistics
- 📈 **Reports**: Generate trading operation statistics
- 🔄 **Fallback Providers**: Automatic switching between data sources

## Technology Stack

- **Python 3.11+** — main language
- **uv** — dependency and package manager
- **SQLite** — data and recommendations storage
- **Ollama** — local or remote LLM provider
- **Rich** — beautiful CLI interface
- **Pydantic** — data validation and settings

## Architectural Principles

1. **Clean Architecture**: Core (`core`) does not depend on external integrations
2. **Ports & Adapters**: All external dependencies are isolated through interfaces
3. **Dependency Injection**: Components are created and wired in one place
4. **Testability**: Each layer can be tested independently

## Project Structure

```
src/
├── core/           # Domain logic (models, ports, services)
├── data_providers/ # Adapters for market data retrieval
├── news_providers/ # Adapters for news retrieval
├── features/       # Technical indicator calculation
├── agents/         # LLM agents for analysis
├── llm/            # LLM providers (Ollama)
├── storage/        # Repositories and storage
├── runtime/        # Orchestration and jobs
├── ui/             # CLI interface
└── app/            # Entry point and settings
```

## Quick Start

1. **Install dependencies:**
   ```bash
   uv sync --all-extras
   ```

2. **Configure environment:**
   Create a `.env` file with necessary API keys

3. **Initialize database:**
   ```bash
   python src/app/main.py init-db
   ```

4. **Run analysis:**
   ```bash
   python src/app/main.py analyze --symbol EURUSD --timeframe 1h
   ```

## Supported Providers

### Market Data
- **OANDA** — primary provider for Forex
- **Twelve Data** — fallback provider

### News
- **GDELT** — global news database
- **NewsAPI** — news aggregator (planned)

### LLM
- **Ollama** — local or remote server

## Security

The system includes a safety policy that validates recommendations before issuing them. See [Safety Policy](safety_policy.md) for details.

## Future Development

- Cryptocurrency support
- Broker integration for automated trading
- Web interface
- Advanced analytics and visualization