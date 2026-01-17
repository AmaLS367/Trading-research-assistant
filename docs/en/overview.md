# 📊 Trading Research Assistant - Overview

**LLM-powered automated financial market analysis system**

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![uv](https://img.shields.io/badge/uv-Latest-FFD43B?logo=python&logoColor=black)](https://github.com/astral-sh/uv)
[![Architecture](https://img.shields.io/badge/Architecture-Clean%20Architecture-4ECDC4)](./architecture.md)

---

## What is this?

**Trading Research Assistant** is a production-ready automated financial market analysis system that uses Large Language Models (LLM) to generate trading recommendations based on technical and fundamental analysis. Built with clean architecture principles and designed for extensibility.

---

## ✨ Key Features

- 📊 **Technical Analysis** - Automatic indicator calculation and chart analysis via LLM
- 📰 **Fundamental Analysis** - News aggregation and analysis from various sources
- 🤖 **LLM Agents** - Use of local or remote LLM models for analysis
- 💾 **Trade Journal** - Track trading results and statistics
- 📈 **Reports** - Generate trading operation statistics
- 🔄 **Fallback Providers** - Automatic switching between data sources
- 🏗️ **Clean Architecture** - Domain-driven design with ports & adapters pattern
- 🧪 **Testable** - Each layer can be tested independently

---

## 🛠️ Technology Stack

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

---

## 🏗️ Architectural Principles

1. **Clean Architecture** - Core (`core`) does not depend on external integrations
2. **Ports & Adapters** - All external dependencies are isolated through interfaces
3. **Dependency Injection** - Components are created and wired in one place
4. **Testability** - Each layer can be tested independently

For detailed architecture documentation, see [Architecture](./architecture.md).

---

## 📁 Project Structure

```
src/
├── core/              # Domain logic (models, ports, services, policies)
├── data_providers/    # Adapters for market data retrieval
├── news_providers/    # Adapters for news retrieval
├── features/          # Technical indicator calculation
├── agents/            # LLM agents for analysis
├── llm/               # LLM providers (Ollama)
├── storage/           # Repositories and storage
├── runtime/           # Orchestration and jobs
├── ui/                # CLI interface
├── app/               # Entry point and settings
├── broker_journal/    # Trade journal management
└── utils/             # Utilities (logging, retry, time)
```

For detailed structure, see [Architecture Documentation](./architecture.md).

---

## 🚀 Quick Start

1. **Create and activate virtual environment:**
   
   **Windows (PowerShell):**
   ```powershell
   uv venv --python 3.11
   .venv\Scripts\Activate.ps1
   ```
   
   **Linux/macOS:**
   ```bash
   uv venv --python 3.11
   source .venv/bin/activate
   ```

2. **Install dependencies:**
   ```bash
   uv sync --extra dev
   ```

3. **Configure environment:**
   Copy `.env.example` to `.env` and fill in your API keys (see [Usage Guide](./usage_guide.md) for details)

4. **Initialize database:**
   ```bash
   python src/app/main.py init-db
   ```

5. **Run analysis:**
   ```bash
   python src/app/main.py analyze --symbol EURUSD --timeframe 1h
   ```

For detailed installation and usage instructions, see [Usage Guide](./usage_guide.md).

---

## 🌐 Supported Providers

### Market Data
- **OANDA** — primary provider for Forex
- **Twelve Data** — fallback provider

### News
- **GDELT** — global news database
- **NewsAPI** — news aggregator

### LLM
- **Ollama** — local or remote server

---

## 🔒 Security

The system includes a safety policy that validates recommendations before issuing them. See [Safety Policy](./safety_policy.md) for details.

⚠️ **Important**: Trading Research Assistant is a research and analysis tool, not an automated trading system. The system does not guarantee recommendation profitability. All trading decisions are made by the user independently.

---

## 📚 Documentation

- 📖 [Overview](./overview.md) - This document
- 🏗️ [Architecture](./architecture.md) - Project structure and design patterns
- 📚 [Usage Guide](./usage_guide.md) - Installation and usage instructions
- ⚙️ [Environment Configuration](./env_configuration.md) - Complete description of all .env variables
- 🤖 [LLM Task Routing](./llm_task_routing.md) - LLM routing by tasks and branches
- 🔧 [Troubleshooting](./troubleshooting.md) - Common issues and solutions
- 🔒 [Safety Policy](./safety_policy.md) - Safety policy and risk management
- 📋 [Import Rules](./import_rules.md) - Import rules and dependency graph
- 🗺️ [Roadmap](./roadmap.md) - Planned improvements and enhancements

---

## 🔮 Future Development

- Cryptocurrency support
- Broker integration for automated trading
- Web interface
- Advanced analytics and visualization

---

[📖 Back to README](../../README.md) | [🏗️ Architecture](./architecture.md) | [📚 Usage Guide](./usage_guide.md)
