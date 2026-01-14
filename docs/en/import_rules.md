# 📋 Import Rules and Dependency Graph

**Module dependency rules and architecture constraints**

[![Architecture](https://img.shields.io/badge/Architecture-Clean%20Architecture-4ECDC4)](./architecture.md)

---

## Goal

Core doesn't know about external integrations. External modules know about core and implement its interfaces.

---

## ✅ Allowed Dependency Graph

```
app -> runtime -> (features, agents, broker_journal, storage, data_providers, news_providers, llm) -> core

core -> only stdlib and its subpackages core/*
core/ports -> only stdlib
```

---

## 🚫 Forbidden Directions

* `core` does NOT import `data_providers`, `news_providers`, `storage`, `llm`, `ui`, `runtime`, `app`
* `features` does NOT import `providers`, `storage`, `runtime`, `app`, `ui`
* `agents` does NOT import `storage`, `runtime`, `app`, `ui`
* `data_providers`, `news_providers`, `llm` do NOT import each other directly
* `storage` does NOT import `runtime`, `app`, `ui`
* `ui` does NOT import `providers` directly (only `runtime` and `core.models` for display)

---

## Import Rules by Module

### 1) `src/core/` (domain)

**Can import:**

* stdlib
* `core.models/*`
* `core.policies/*`
* `core.ports/*`
* `core.services/*`

**Cannot import:**

* everything else, including `features` and `agents`

**Why:**

* `core` remains clean and portable
* change provider or LLM, `core` stays untouched

---

### 2) `src/core/models/`

* No external imports
* Maximum: stdlib, `typing`, `dataclasses` or `pydantic` (if we decide)

---

### 3) `src/core/ports/` (interfaces)

**Imports:**

* stdlib
* `core.models` (argument types and return types)

**Does not import:**

* implementations (`providers`, `storage`, `llm`)

---

### 4) `src/core/services/`

**Imports:**

* `core.models`
* `core.ports`
* `core.policies`

**Example logic:**

* `Orchestrator` accepts ports (`MarketDataProvider`, `NewsProvider`, `LlmProvider`, `Storage`) and connects the pipeline, but doesn't know specific implementations.

---

### 5) `src/features/`

**Imports:**

* stdlib
* `core.models` (`Candle`, `Timeframe`)
* its subpackages `features/*`

**Does not import:**

* `providers`, `storage`, `agents`, `runtime`

---

### 6) `src/agents/`

**Imports:**

* stdlib
* `core.models` (`Recommendation`, `Rationale`, `DecisionContext`)
* `features.snapshots` (`FeatureSnapshot`)
* `core.ports.llm_provider` (to call LLM through interface)

**Does not import:**

* `storage` (agents don't write to DB)
* `runtime` (agents don't manage the loop)

---

### 7) `src/data_providers/`

**Imports:**

* stdlib
* `core.models` (`Candle`, `Timeframe`)
* `core.ports.market_data_provider` (to implement the interface)
* HTTP client and utilities

**Does not import:**

* `features`, `agents`, `runtime`

---

### 8) `src/news_providers/`

**Imports:**

* stdlib
* `core.ports.news_provider`
* its own DTO models if needed, or `core` types

---

### 9) `src/llm/`

**Imports:**

* stdlib
* `core.ports.llm_provider`
* Ollama client or remote HTTP client

**Important:**

* Agents don't care where LLM is. They only see `LlmProvider`.

---

### 10) `src/storage/`

**Imports:**

* stdlib
* `core.ports.storage` (or set of repository ports)
* `core.models` (types we store)
* sqlite drivers and migrations

**Does not import:**

* `runtime`, `ui`, `providers`

---

### 11) `src/broker_journal/`

**Imports:**

* stdlib
* `core.models` (`JournalEntry`, `Outcome`)
* `core.ports.storage` (to write journal and outcomes)

---

### 12) `src/runtime/`

**Imports:**

* `core.services` (`Orchestrator`, `Reporter`, `Scheduler`)
* `core.ports` (all interfaces)
* concrete implementations: `providers`, `llm`, `storage`, `agents`, `features`
* but `runtime` is the only place where it's allowed to glue implementations together

---

### 13) `src/ui/`

**Imports:**

* `runtime` (receives ready data and commands)
* `core.models` (only for display)

---

### 14) `src/app/`

**Imports:**

* `runtime`
* `wiring`
* `settings`

---

## Quick Check to Avoid Cycles

**Rule 1**

* All implementations live outside `core` and implement `core/ports`.

**Rule 2**

* Any dependency on "external" goes only through interface from `core/ports`.

**Rule 3**

* Wiring only in `app` or `runtime`, nowhere else.

---

## Dependency Matrix by Module

### core
* External dependencies: none (only stdlib)

### providers (data_providers, news_providers)
* `httpx` (HTTP client)
* `tenacity` (retry logic)

### features
* `pandas`
* `numpy`
* `ta` (technical indicators)

### agents
* `core.ports.llm_provider` (interface)
* Does not import `llm` directly

### llm
* `ollama` (client)

### storage
* `sqlite3` (stdlib)
* Optionally: drivers for migrations

### ui
* `rich` (CLI formatting)

### runtime
* All of the above (glues implementations together)

### app
* `pydantic-settings` (configuration)

---

[📖 Overview](./overview.md) | [🏗️ Architecture](./architecture.md) | [📚 Usage Guide](./usage_guide.md) | [🔧 Troubleshooting](./troubleshooting.md)
