# 🏗️ Architecture

**Clean Architecture with Ports & Adapters pattern**

[![Architecture](https://img.shields.io/badge/Architecture-Clean%20Architecture-4ECDC4)](./architecture.md)
[![Pattern](https://img.shields.io/badge/Pattern-Ports%20%26%20Adapters-FF6B6B)](./architecture.md)

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
- `Rationale` — recommendation rationale (includes LLM metadata: provider, model, latency, attempts, error)
- `DecisionContext` — decision-making context
- `JournalEntry` — trade journal entry
- `Outcome` — trade outcome
- `Signal` — trading signal
- `Run` — analysis run metadata
- `LlmRequest` — standardized LLM request (task, prompts, temperature, timeout, etc.)
- `LlmResponse` — standardized LLM response (text, provider, model, latency, attempts, error)
- `VerificationReport` — verification results with issues and suggested fixes
- `VerificationIssue` — individual verification issue (code, message, severity, evidence)

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
  - Executes jobs in sequence: Market Data → Features → Technical Analysis → News → News Analysis → Synthesis → Persistence
  - Manages Run lifecycle (PENDING → SUCCESS/FAILED)
  - Returns `run_id` for artifact tracking
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
- `NewsAPIProvider` → `NewsProvider` (used via `MultiNewsProvider` as secondary provider)

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
- `VerifierAgent` — LLM-based verification of agent outputs (optional)

**Dependencies**: `core.ports.llm_provider` (interface), `core.models`, `features.snapshots`, `llm.providers.llm_router`

**Rule**: Agents use `LlmRouter` for LLM calls, which handles provider selection and fallback. Agents don't write to DB and don't manage execution loop.

### 5. LLM Providers (`src/llm/`)

**Purpose**: Implementation of `LlmProvider` for specific LLM services and routing logic.

#### Implementations:
- `OllamaClient` → `LlmProvider` (local or remote Ollama)
- `DeepSeekClient` → `LlmProvider` (DeepSeek API, OpenAI-compatible)
- `LlmRouter` → Task-based routing with fallback chains

#### Router Features:
- **Task-based routing** — Different models for different tasks (tech_analysis, news_analysis, synthesis, verification)
- **Automatic fallback** — Falls back to available providers if primary fails
- **Health checks** — Provider availability checking with caching
- **Last resort** — Falls back to `ollama_local + llama3:latest` if all configured steps fail
- **Per-task overrides** — Optional timeout and temperature overrides per task

**Rule**: Agents don't care where LLM is located — they use `LlmRouter` which abstracts provider selection.

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
  - `JobResult[T]` — generic result type with `ok`, `value`, `error` fields
  - `FetchMarketDataJob` — market data retrieval (returns `JobResult[list[Candle]]`)
  - `FetchNewsJob` — news retrieval (returns `JobResult[NewsDigest]`, falls back to LOW quality on error)
  - `BuildFeaturesJob` — feature calculation (returns `JobResult[tuple[FeatureSnapshot, Signal]]`)
  - `PersistRecommendationJob` — recommendation persistence (saves to DB and artifacts)
  - `RunAgentsJob` — legacy agent execution (kept for parallel existence)
- `loop/` — execution loops:
  - `MinuteLoop` — runs analysis for each symbol on minute boundaries

**Job System**: All jobs return `JobResult` objects instead of raising exceptions. Orchestrator checks `ok` flag and handles failures gracefully.

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

### Orchestrator Pipeline

The `Orchestrator` executes the analysis pipeline:

```
1. Create Run (PENDING status)
2. FetchMarketDataJob → check JobResult.ok
3. BuildFeaturesJob → check JobResult.ok
4. TechnicalAnalyst.analyze() → uses LlmRouter with task="tech_analysis"
5. FetchNewsJob → check JobResult.ok
6. NewsAnalyst.analyze() → uses LlmRouter with task="news_analysis"
7. Synthesizer.synthesize() → uses LlmRouter with task="synthesis"
8. (Optional) VerifierAgent.verify() → uses LlmRouter with task="verification"
   - If verification fails and LLM_VERIFIER_MODE=hard, attempts repair
9. PersistRecommendationJob → check JobResult.ok
10. Update Run to SUCCESS or FAILED
11. Return run_id (for artifact tracking)
```

LLM calls go through `LlmRouter`, which:
- Selects provider based on task routing configuration
- Checks provider health (with caching)
- Falls back to next provider if current fails
- Falls back to `ollama_local + llama3:latest` as last resort
- Returns `LlmResponse` with metadata (provider, model, latency, attempts, error)

If any job fails (`JobResult.ok = False`), the pipeline stops, Run is marked as FAILED, and `run_id` is returned.

### Artifacts

Each run creates artifacts in `artifacts/run_{run_id}/`:
- `recommendation.json` — recommendation data
- `rationales.md` — markdown with all rationales (Technical, News, Synthesis)
- `llm/` — LLM exchange artifacts:
  - `llm/tech_analysis/` — Technical analysis request/response (with secret masking)
  - `llm/news_analysis/` — News analysis request/response
  - `llm/synthesis/` — Synthesis request/response
  - `llm/verification/` — Verification request/response (if enabled)
  - Each task directory contains `request.json`, `response.json`, and `response.txt`

### Legacy Flow (RunAgentsJob)

The old `RunAgentsJob` is kept for parallel existence during transition.

## Dependency Injection

All dependencies are created in `src/app/wiring.py`:

```python
def create_market_data_provider() -> MarketDataProvider:
    # Creates providers and wires them
    return FallbackMarketDataProvider(...)

def create_llm_providers() -> dict[str, LlmProvider]:
    # Creates OllamaClient (local/server) and DeepSeekClient (if configured)
    # Returns mapping: provider_name -> LlmProvider instance

def create_llm_router() -> LlmRouter:
    # Creates LlmRouter with:
    # - providers dict from create_llm_providers()
    # - routing_config from settings
    # - task_routings for each task (tech, news, synthesis, verification)

def create_technical_analyst() -> TechnicalAnalyst:
    llm_router = create_llm_router()
    return TechnicalAnalyst(llm_router=llm_router)
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

[📖 Overview](./overview.md) | [📚 Usage Guide](./usage_guide.md) | [🔧 Troubleshooting](./troubleshooting.md) | [📋 Import Rules](./import_rules.md)