# Code Review Report: Trading Research Assistant

**Review Date:** 2026-01-17  
**Reviewer Role:** Senior Software Architect / Principal Code Reviewer  
**Review Scope:** Architecture, maintainability, testability, readability, reliability  

---

## A) Architecture Snapshot

### Entry Points

**CLI (`src/app/main.py`):**
- Single entry point via `trading-assistant` script (defined in `pyproject.toml`)
- Commands: `init-db`, `analyze`, `loop`, `show-latest`, `journal`, `report`
- Uses `argparse` for CLI parsing, `rich` for console output

### Layer Structure

```
┌─────────────────────────────────────────────────────────────────────┐
│                         src/app/                                     │
│  main.py (CLI)  ←  wiring.py (DI)  ←  settings.py (Config)         │
│  logging_config.py (Loguru setup)                                   │
└────────────────────────────┬────────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────────┐
│                       src/runtime/                                   │
│  orchestrator.py (RuntimeOrchestrator - ~650 lines, main pipeline)  │
│  loop/minute_loop.py (Loop runner)                                  │
│  preflight.py (GPU/model checks)                                    │
│  jobs/ (FetchMarketData, BuildFeatures, FetchNews, PersistRec)      │
└────────────────────────────┬────────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────────┐
│                        src/agents/                                   │
│  technical_analyst.py, news_analyst.py, synthesizer.py, verifier.py │
│  prompts/ (System prompts for each agent)                           │
└────────────────────────────┬────────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────────┐
│                         src/llm/                                     │
│  providers/llm_router.py (Routing logic with fallbacks)             │
│  ollama/ollama_client.py, deepseek/deepseek_client.py               │
└────────────────────────────┬────────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────────┐
│                       src/core/                                      │
│  models/ (Candle, Recommendation, Run, Rationale, News, etc.)       │
│  ports/ (LlmProvider, Storage, MarketDataProvider, NewsProvider)    │
│  policies/ (SafetyPolicy, constraints)                              │
│  services/ (Scheduler, Reporter)                                    │
└─────────────────────────────────────────────────────────────────────┘
```

### Provider Layer

- **Market Data:** `OandaProvider`, `TwelveDataProvider`, `FallbackMarketDataProvider`
- **News:** `GDELTProvider`, `NewsAPIProvider`, `MultiNewsProvider`
- **LLM:** `OllamaClient`, `DeepSeekClient` (routed via `LlmRouter`)
- **Storage:** `SqliteStorage` with repositories pattern

### Responsibility Boundaries

**Well-defined:**
- `core/ports/` defines clean interfaces (Protocol classes)
- `core/models/` contains pure data models (Pydantic)
- Providers implement ports without cross-dependencies
- Storage uses repository pattern with clear separation

**Boundary Violations Found:**
1. `settings` singleton imported directly in 6 files beyond `app/wiring.py`
2. `RuntimeOrchestrator` (~650 lines) mixes orchestration, artifact saving, and repair loops
3. `main.py` creates some repositories directly instead of via `wiring.py`

---

## B) Seniority Scorecard (0-5)

| Criterion | Score | Comment |
|-----------|-------|---------|
| **Architectural Boundaries** | 3.5/5 | Ports pattern good, but `settings` leaks across layers; orchestrator is overloaded |
| **Config/Env Management** | 4/5 | Excellent env schema with 100+ vars, good validation, good docs. Minor: timeout hierarchy is complex |
| **Contracts/Types/DTO** | 4/5 | Pydantic models, Protocol interfaces, type hints. Some `dict[str, Any]` in debug payloads |
| **Errors/Logs/Observability** | 4/5 | Loguru with sanitization, structured JSON logs, stage timers. No bare `except:` found |
| **Testability/Safety Net** | 3.5/5 | 215 tests, good unit coverage for core. Missing: contract tests for providers, no mocking strategy doc |
| **Readability/Style Consistency** | 3.5/5 | Consistent formatting (ruff), some long methods (orchestrator), duplicate JSON extraction logic |
| **Extensibility** | 4/5 | Adding provider is clean (implement port). LLM router extensible. News provider pattern good |
| **Documentation as Specification** | 4/5 | Detailed docs for env vars, routing, architecture. Minor inconsistencies with code defaults |

**Overall Seniority Score: 3.75/5** — Solid intermediate-to-senior level codebase with clear architectural intent. Main gaps are in separation of concerns within orchestrator and some code duplication.

---

## C) Top 12 Issues

### Issue #1: RuntimeOrchestrator is a God Object
**Severity:** HIGH  
**Evidence:** `src/runtime/orchestrator.py` (657 lines), `run_analysis()` method (~550 lines)  
**Impact:** Hard to test, hard to extend, violates SRP  
**Risk:** Low (refactoring is behavior-preserving if done carefully)

### Issue #2: Settings Singleton Leaks Across Layers
**Severity:** HIGH  
**Evidence:** Direct `from src.app.settings import settings` in:
- `src/runtime/orchestrator.py` (timeout lookups)
- `src/runtime/loop/minute_loop.py`
- `src/llm/providers/llm_router.py` (last_resort, timeouts)
**Impact:** Tight coupling, harder to test, violates dependency inversion  
**Risk:** Low (can inject settings via constructor)

### Issue #3: Duplicate `_extract_json()` Logic
**Severity:** MEDIUM  
**Evidence:** 
- `src/agents/synthesizer.py:230-257`
- `src/agents/verifier.py:105-129`
**Impact:** Bug fixes must be applied twice, inconsistency risk  
**Risk:** Very low (pure function extraction)

### Issue #4: `main.py` Bypasses Wiring Layer
**Severity:** MEDIUM  
**Evidence:** `src/app/main.py:33-38` creates `DBConnection` and repositories directly at module level  
**Impact:** Inconsistent initialization, harder to test main module  
**Risk:** Low (move to lazy initialization or wiring)

### Issue #5: Missing Abstract Methods on LlmProvider
**Severity:** MEDIUM  
**Evidence:** `src/core/ports/llm_provider.py` - `generate_with_request()` is concrete, not abstract  
**Impact:** Subclasses may not override correctly, contract unclear  
**Risk:** Very low (add @abstractmethod)

### Issue #6: Verifier Mode "hard" Logic Embedded in Orchestrator
**Severity:** MEDIUM  
**Evidence:** `src/runtime/orchestrator.py:477-598` - repair loop logic  
**Impact:** Hard to test repair logic in isolation, orchestrator complexity  
**Risk:** Medium (behavior change if extracted incorrectly)

### Issue #7: No Retry/Backoff on DB Operations
**Severity:** MEDIUM  
**Evidence:** `src/storage/sqlite/repositories/*.py` - no retry decorators  
**Impact:** Transient SQLite lock errors on Windows could crash pipeline  
**Risk:** Low (add retry wrapper)

### Issue #8: `warnings.warn()` Used Instead of Logger
**Severity:** LOW  
**Evidence:** `src/data_providers/forex/fallback_provider.py:42`  
**Impact:** Inconsistent with loguru logging strategy, not captured in log files  
**Risk:** Very low

### Issue #9: FallbackMarketDataProvider Swallows Exception Type
**Severity:** LOW  
**Evidence:** `src/data_providers/forex/fallback_provider.py:34` - catches generic `Exception`  
**Impact:** Might mask programming errors vs network errors  
**Risk:** Low (narrow exception type)

### Issue #10: Docs Say `LLM_VERIFIER_ENABLED` Default is `false`, Code Says `False`
**Severity:** LOW  
**Evidence:** 
- `docs/en/env_configuration.md:162` says "Default value: `false`"
- `src/app/settings.py:78` has `llm_verifier_enabled: ... = False`
- Consistent, but `.env.example:77` has `LLM_VERIFIER_ENABLED=true`
**Impact:** User confusion about defaults  
**Risk:** Very low

### Issue #11: Magic Strings for Task Names
**Severity:** LOW  
**Evidence:** `llm_router.py:134-138` duplicates task prefix mapping that exists in `_get_timeout_for_task()`  
**Impact:** Easy to get out of sync  
**Risk:** Very low (extract to constant or use single source)

### Issue #12: No Type Stub for `_parse_verification_response` Parameter
**Severity:** LOW  
**Evidence:** `src/agents/verifier.py:29` - `llm_response` parameter has no type hint  
**Impact:** IDE/mypy cannot validate usage  
**Risk:** Very low

---

## D) Patch Plan (3 Phases)

### Phase 1: Safety Net (Testing & Validation)

#### Task 1.1: Add Contract Tests for LlmProvider Implementations
**Files:** `tests/unit/llm/test_ollama_contract.py`, `tests/unit/llm/test_deepseek_contract.py`  
**Changes:** Create parameterized tests that verify each provider satisfies `LlmProvider` protocol  
**Acceptance:** `pytest tests/unit/llm/test_*_contract.py` passes  
**Verification:** `uv run pytest tests/unit/llm/ -v`

#### Task 1.2: Add Integration Test for Orchestrator Pipeline Stages
**Files:** `tests/integration/runtime/test_orchestrator_stages.py`  
**Changes:** Test each stage (fetch_market, build_features, tech_analysis, etc.) can be called independently with mocks  
**Acceptance:** Coverage of orchestrator methods > 60%  
**Verification:** `uv run pytest tests/integration/runtime/test_orchestrator_stages.py --cov=src.runtime.orchestrator`

#### Task 1.3: Add Snapshot Tests for LLM Prompt Templates
**Files:** `tests/unit/agents/test_prompt_snapshots.py`  
**Changes:** Snapshot test each prompt function to catch accidental changes  
**Acceptance:** Snapshots stored in `tests/snapshots/`  
**Verification:** `uv run pytest tests/unit/agents/test_prompt_snapshots.py`

#### Task 1.4: Add Pre-commit Hook for Import Rule Validation
**Files:** `scripts/python/check_imports.py`, `.pre-commit-config.yaml` (new)  
**Changes:** Script that validates import rules from `docs/en/import_rules.md`  
**Acceptance:** `python scripts/python/check_imports.py` exits 0 on clean repo  
**Verification:** Manual run + CI integration

---

### Phase 2: Architecture Straightening

#### Task 2.1: Extract JSON Parsing Utilities
**Files:** `src/utils/json_helpers.py` (new), update `synthesizer.py`, `verifier.py`  
**Changes:** 
- Create `extract_json_from_llm_response(text: str) -> str`
- Create `try_fix_json(text: str) -> str | None`
- Replace duplicate code in agents
**Acceptance:** No duplicate `_extract_json` methods; all tests pass  
**Verification:** `uv run pytest tests/unit/agents/`

#### Task 2.2: Inject Settings into LlmRouter
**Files:** `src/llm/providers/llm_router.py`, `src/app/wiring.py`  
**Changes:**
- Add `last_resort: RouteCandidate` and `timeout_config` params to `LlmRouter.__init__`
- Remove direct `settings` import from `llm_router.py`
- Update `create_llm_router()` in wiring
**Acceptance:** `llm_router.py` has no `from src.app.settings import settings`  
**Verification:** `uv run pytest tests/unit/llm/`

#### Task 2.3: Extract RepairLoop from Orchestrator
**Files:** `src/runtime/repair_loop.py` (new), update `orchestrator.py`  
**Changes:**
- Create `RepairLoop` class with `attempt_repairs()` method
- Move lines 477-598 from orchestrator
- Orchestrator calls `RepairLoop` if verifier_mode == "hard"
**Acceptance:** `orchestrator.py` < 500 lines; repair logic testable independently  
**Verification:** `uv run pytest tests/unit/runtime/test_verification_hard_mode.py`

#### Task 2.4: Lazy Initialization in main.py
**Files:** `src/app/main.py`  
**Changes:**
- Remove module-level `db = DBConnection(...)` and repository instantiations
- Create `get_db()`, `get_rec_repo()` functions or use wiring module
**Acceptance:** No module-level side effects in main.py  
**Verification:** `uv run python -c "import src.app.main"` succeeds without .env

#### Task 2.5: Add @abstractmethod to LlmProvider.generate_with_request
**Files:** `src/core/ports/llm_provider.py`  
**Changes:**
- Make `generate_with_request()` abstract or split into `BaseLlmProvider` with mixin
- Ensure all implementations override
**Acceptance:** mypy passes; no runtime errors  
**Verification:** `uv run mypy src/core/ports/llm_provider.py`

---

### Phase 3: Polish (Logs, Errors, Docs, Consistency)

#### Task 3.1: Replace warnings.warn with Logger
**Files:** `src/data_providers/forex/fallback_provider.py`  
**Changes:**
- Import `get_logger` from `src.utils.logging`
- Replace `warnings.warn()` with `logger.warning()`
**Acceptance:** No `warnings.warn` in src/  
**Verification:** `rg "warnings.warn" src/`

#### Task 3.2: Narrow Exception Types in FallbackProvider
**Files:** `src/data_providers/forex/fallback_provider.py`  
**Changes:**
- Catch `(httpx.HTTPError, ValueError, ConnectionError)` instead of `Exception`
- Let programming errors propagate
**Acceptance:** Tests still pass; unexpected errors not swallowed  
**Verification:** `uv run pytest tests/unit/data_providers/`

#### Task 3.3: Add Retry to SQLite Repositories
**Files:** `src/storage/sqlite/repositories/*.py`, `src/utils/retry.py`  
**Changes:**
- Add `@retry_transient_db_error` decorator to save/update methods
- Decorator handles `sqlite3.OperationalError` with "database is locked"
**Acceptance:** Repositories can recover from transient locks  
**Verification:** Manual test with concurrent access or unit test with mock

#### Task 3.4: Fix .env.example vs Code Default Discrepancy
**Files:** `.env.example`  
**Changes:**
- Change `LLM_VERIFIER_ENABLED=true` to `LLM_VERIFIER_ENABLED=false` (match code default)
- Add comment explaining when to enable
**Acceptance:** .env.example defaults match settings.py defaults  
**Verification:** Manual review

#### Task 3.5: Consolidate Task Prefix Mapping
**Files:** `src/core/ports/llm_tasks.py`, `src/llm/providers/llm_router.py`, `src/runtime/orchestrator.py`  
**Changes:**
- Add `TASK_TO_PREFIX: dict[str, str]` constant in `llm_tasks.py`
- Replace inline dicts in router and orchestrator
**Acceptance:** Single source of truth for task-to-prefix mapping  
**Verification:** `rg "task_prefix_map" src/` returns only import lines

#### Task 3.6: Add Type Hint to verifier._parse_verification_response
**Files:** `src/agents/verifier.py`  
**Changes:**
- Change `llm_response` to `llm_response: LlmResponse`
- Add import if needed
**Acceptance:** mypy passes  
**Verification:** `uv run mypy src/agents/verifier.py`

---

## E) Quick Wins (Low-Risk, Behavior-Preserving)

1. **Extract `_extract_json()` to utils** (Task 2.1) — Pure function, no behavior change, eliminates duplication

2. **Replace `warnings.warn` with logger** (Task 3.1) — One-line change, consistent logging

3. **Add type hint to verifier method** (Task 3.6) — Documentation improvement, no runtime change

4. **Consolidate task prefix mapping** (Task 3.5) — Reduces magic strings, no behavior change

5. **Fix .env.example default** (Task 3.4) — Documentation accuracy, no code change

---

## Special Checks Summary

### Circular Dependencies
**Status:** ✅ None found  
The import rules documented in `docs/en/import_rules.md` are respected. Core does not import providers/runtime.

### Settings Leakage ("Сквозные импорты")
**Status:** ⚠️ Found in 6 files  
`settings` singleton imported in `orchestrator.py`, `minute_loop.py`, `llm_router.py`, `logging_config.py`, `wiring.py`, `main.py`. Should be injected.

### Docs vs Code Discrepancies
**Status:** ⚠️ Minor  
- `.env.example` has `LLM_VERIFIER_ENABLED=true`, code default is `False`
- Timeout priority documented correctly

### Bare `except:` or `except ... pass`
**Status:** ✅ None found  
All exception handlers are typed or re-raise. `KeyboardInterrupt` catch in `minute_loop.py` with `pass` is intentional and acceptable.

### Hardcoded Values That Should Be Config
**Status:** ✅ Acceptable  
- Health check TTL (30 seconds) in `llm_router.py` — could be config but reasonable default
- Invalid hostnames list in `settings.py` — intentional validation, not config

---

## Conclusion

The codebase demonstrates solid architectural thinking with clean port/adapter patterns, comprehensive configuration, and good test coverage. The main improvement opportunities are:

1. **Reduce orchestrator complexity** — Extract repair loop, split large method
2. **Eliminate settings leakage** — Inject dependencies instead of importing singleton
3. **Consolidate utilities** — JSON extraction, task mappings

These changes would raise the seniority perception from "strong intermediate" to "clearly senior" without changing behavior.
