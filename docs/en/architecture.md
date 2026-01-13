<div align="center">

# 🏗️ Architecture

**Clean Architecture with Ports & Adapters pattern**

[![Architecture](https://img.shields.io/badge/Architecture-Clean%20Architecture-4ECDC4)](./architecture.md)
[![Pattern](https://img.shields.io/badge/Pattern-Ports%20%26%20Adapters-FF6B6B)](./architecture.md)

</div>

---

## General Concept

The project is built on **Clean Architecture** principles using the **Ports & Adapters** pattern. The system core (`core`) is completely isolated from external dependencies and only knows about business logic.

## Dependency Graph

```
app → runtime → (features, agents, storage, providers, llm) → core
```

**Key Rule**: `core` does not know about external integrations. External modules implement interfaces from `core/ports`.

## Architecture Layers

### 1. Core (`src/core/`)

**Purpose**: Domain logic without external dependencies (stdlib only).

#### `core/models/`
Domain data models:
- `Candle` — OHLCV candle data
- `Timeframe` — timeframe (1m, 5m, 1h, 1d, etc.)
- `Recommendation` — trading recommendation
- `Rationale` — recommendation rationale
- `DecisionContext` — decision-making context
- `JournalEntry` — trade journal entry
- `Outcome` — trade outcome
- `Signal` — trading signal
- `Run` — analysis run metadata

#### `core/ports/`
Abstract interfaces (ABC) for external dependencies:
- `MarketDataProvider` — market data retrieval
- `NewsProvider` — news retrieval
- `LlmProvider` — LLM interaction
- `Storage` — repository interfaces
- `Clock` — time abstraction

#### `core/policies/`
Business rules and policies:
- `SafetyPolicy` — recommendation safety checks
- `Constraints` — constraints and validation

#### `core/services/`
Domain services:
- `Orchestrator` — analysis pipeline orchestration
- `Reporter` — report generation
- `Scheduler` — task scheduling

**Rule**: `core` does not import anything external except stdlib.

### 2. Data Providers (`src/data_providers/`, `src/news_providers/`)

**Purpose**: Implementation of interfaces from `core/ports` for external data retrieval.

#### Implementations:
- `OandaProvider` → `MarketDataProvider`
- `TwelveDataProvider` → `MarketDataProvider`
- `FallbackMarketDataProvider` → automatic switching between providers
- `GDELTProvider` → `NewsProvider`
- `NewsAPIProvider` → `NewsProvider` (planned)

**Rule**: Providers don't know about each other and don't import `features`, `agents`, `runtime`.

### 3. Feature Calculation (`src/features/`)

**Purpose**: Technical indicator calculation and market data analysis.

#### Modules:
- `indicators/` — indicator calculation (RSI, MACD, Bollinger Bands, etc.)
- `volatility/` — volatility estimation
- `regime/` — market regime detection (trend, flat)
- `snapshots/` — feature snapshots for agent consumption

**Dependencies**: `pandas`, `numpy`, `ta`, `core.models`

**Rule**: `features` doesn't know about providers, storage, and runtime.

### 4. LLM Agents (`src/agents/`)

**Purpose**: Using LLM for analysis and recommendation generation.

#### Agents:
- `TechnicalAnalyst` — technical analysis via LLM
- `Synthesizer` — final recommendation synthesis
- `NewsAnalyst` — news analysis and aggregation
- `NewsSentimentAnalyst` — news sentiment analysis

**Dependencies**: `core.ports.llm_provider` (interface), `core.models`, `features.snapshots`

**Rule**: Agents don't write to DB and don't manage execution loop.

### 5. LLM Providers (`src/llm/`)

**Purpose**: Implementation of `LlmProvider` for specific LLM services.

#### Implementations:
- `OllamaClient` → `LlmProvider` (local or remote Ollama)

**Rule**: Agents don't care where LLM is located — they only see the interface.

### 6. Storage (`src/storage/`)

**Purpose**: Data persistence via SQLite.

#### Components:
- `sqlite/repositories/` — repositories for various entities
- `sqlite/connection.py` — connection management
- `sqlite/migrations/` — database migrations
- `artifacts/` — report and log storage

**Rule**: `storage` doesn't know about `runtime`, `ui`, `providers`.

### 7. Orchestration (`src/runtime/`)

**Purpose**: Wiring all components together and executing tasks.

#### Components:
- `jobs/` — execution tasks:
  - `FetchMarketDataJob` — market data retrieval
  - `FetchNewsJob` — news retrieval
  - `BuildFeaturesJob` — feature calculation
  - `RunAgentsJob` — agent execution
  - `PersistRecommendationJob` — recommendation persistence
- `loop/` — execution loops (e.g., `MinuteLoop`)

**Rule**: `runtime` is the only place where concrete implementations can be wired together.

### 8. Entry Point (`src/app/`)

**Purpose**: Application initialization and CLI interface.

#### Components:
- `main.py` — CLI commands
- `wiring.py` — Dependency Injection (component creation and wiring)
- `settings.py` — configuration via pydantic-settings

**Rule**: `app` knows about `runtime` and uses `wiring` to create dependencies.

### 9. Interface (`src/ui/`)

**Purpose**: Displaying data to the user.

#### Components:
- `cli/dashboard.py` — CLI dashboard
- `cli/renderers/` — renderers for various data types

**Dependencies**: `rich` for formatting

**Rule**: `ui` doesn't import providers directly, only `runtime` and `core.models`.

## Analysis Execution Flow

```
1. CLI (main.py)
   └─> analyze(symbol, timeframe)
       └─> wiring.py creates components
           └─> RunAgentsJob.run()
               ├─> FetchMarketDataJob → retrieves candles
               ├─> BuildFeaturesJob → calculates indicators
               ├─> TechnicalAnalyst → analyzes via LLM
               ├─> FetchNewsJob → retrieves news
               ├─> Synthesizer → synthesizes recommendation
               └─> PersistRecommendationJob → saves to DB
```

## Dependency Injection

All dependencies are created in `src/app/wiring.py`:

```python
def create_market_data_provider() -> MarketDataProvider:
    # Creates providers and wires them
    return FallbackMarketDataProvider(...)

def create_technical_analyst() -> TechnicalAnalyst:
    llm_provider = create_llm_provider()
    return TechnicalAnalyst(llm_provider=llm_provider)
```

This allows:
- Easy implementation swapping
- Isolated component testing
- Avoiding circular dependencies

## Architecture Benefits

1. **Testability**: Core can be tested without external dependencies
2. **Extensibility**: New providers are added by implementing interfaces
3. **Portability**: Core is not tied to specific technologies
4. **Isolation**: Changes in external layers don't affect core
5. **Readability**: Clear separation of concerns

## Import Rules

For detailed import rules and dependency graph, see [Import Rules](./import_rules.md).

---

## Extending the System

### Adding a New Data Provider

1. Create a class implementing `MarketDataProvider`
2. Add creation to `wiring.py`
3. Core remains unchanged

### Adding a New Agent

1. Create a class in `src/agents/`
2. Use `LlmProvider` through interface
3. Add to `RunAgentsJob` if needed

### Adding a New Indicator

1. Add calculation to `features/indicators/`
2. Update `FeatureSnapshot` if needed
3. Agents automatically receive new data

---

<div align="center">

[📖 Overview](./overview.md) • [📚 Usage Guide](./usage_guide.md) • [📋 Import Rules](./import_rules.md)

</div>