# 📚 Usage Guide

**Installation and usage instructions**

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![uv](https://img.shields.io/badge/uv-Latest-FFD43B?logo=python&logoColor=black)](https://github.com/astral-sh/uv)

---

## Installation

### Requirements

- Python 3.11 or higher
- uv (recommended) or pip
- Ollama (for LLM features)
- API keys for data providers

### Installing Dependencies

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

## Configuration

### Environment Variables

Create a `.env` file in the project root:

```bash
# --- Application ---
APP_ENV=development
APP_TIMEZONE=Asia/Yerevan

# --- OANDA API (primary provider) ---
OANDA_API_KEY=your_oanda_api_key_here
OANDA_ACCOUNT_ID=your_account_id
OANDA_BASE_URL=https://api-fxpractice.oanda.com

# --- Twelve Data API (fallback provider) ---
TWELVE_DATA_API_KEY=your_twelve_data_key
TWELVE_DATA_BASE_URL=https://api.twelvedata.com

# --- GDELT API (news) ---
GDELT_BASE_URL=https://api.gdeltproject.org

# --- NewsAPI (optional) ---
NEWSAPI_API_KEY=your_newsapi_key
NEWSAPI_BASE_URL=https://newsapi.org

# --- LLM Providers (Multi-provider routing) ---
# Ollama Local (default fallback)
OLLAMA_LOCAL_URL=http://localhost:11434
OLLAMA_MODEL=llama3:latest

# Ollama Server (optional remote)
OLLAMA_SERVER_URL=http://server:11434

# DeepSeek API (optional)
DEEPSEEK_API_KEY=your_deepseek_api_key
DEEPSEEK_API_BASE=https://api.deepseek.com

# LLM Router Configuration
LLM_ROUTER_MODE=sequential
LLM_VERIFIER_ENABLED=false
LLM_VERIFIER_MODE=soft
LLM_VERIFIER_MAX_REPAIRS=1
LLM_MAX_RETRIES=3
LLM_TIMEOUT_SECONDS=60.0
LLM_TEMPERATURE=0.2

# Task-specific routing (optional, falls back to ollama_local + llama3:latest)
TECH_PRIMARY_PROVIDER=deepseek_api
TECH_PRIMARY_MODEL=deepseek-chat
TECH_FALLBACK1_PROVIDER=ollama_server
TECH_FALLBACK1_MODEL=qwen2.5:32b

NEWS_PRIMARY_PROVIDER=ollama_local
NEWS_PRIMARY_MODEL=llama3:latest

SYNTHESIS_PRIMARY_PROVIDER=deepseek_api
SYNTHESIS_PRIMARY_MODEL=deepseek-chat

VERIFIER_PRIMARY_PROVIDER=ollama_local
VERIFIER_PRIMARY_MODEL=llama3:latest

# Per-task overrides (optional)
TECH_TIMEOUT_SECONDS=120.0
TECH_TEMPERATURE=0.3
NEWS_TIMEOUT_SECONDS=60.0
NEWS_TEMPERATURE=0.2
SYNTHESIS_TIMEOUT_SECONDS=90.0
SYNTHESIS_TEMPERATURE=0.2
VERIFIER_TIMEOUT_SECONDS=60.0
VERIFIER_TEMPERATURE=0.1

# --- Storage ---
STORAGE_SQLITE_DB_PATH=db/forex_research_assistant.sqlite3
STORAGE_ARTIFACTS_DIR=artifacts
STORAGE_MIGRATION_PATH=src/storage/sqlite/migrations/0001_init.sql

# --- Runtime settings ---
RUNTIME_MVP_SYMBOLS_RAW=EURUSD,GBPUSD,USDJPY
RUNTIME_MVP_TIMEFRAME=1h
RUNTIME_MVP_EXPIRY_SECONDS=300
RUNTIME_LLM_ENABLED=true
RUNTIME_LLM_CALL_INTERVAL_SECONDS=300
RUNTIME_NEWS_REFRESH_INTERVAL_SECONDS=300
RUNTIME_MARKET_DATA_WINDOW_CANDLES=300
```

### Database Initialization

Before first use, initialize the database:

```bash
python src/app/main.py init-db
```

This command will create the SQLite database and apply migrations.

## Main Commands

<details>
<summary><strong>📋 Quick Command Reference</strong></summary>

| Command | Description | Example |
|---------|-------------|---------|
| `init-db` | Initialize database | `python src/app/main.py init-db` |
| `analyze` | Run analysis | `python src/app/main.py analyze --symbol EURUSD --timeframe 1h` |
| `show-latest` | View latest recommendation | `python src/app/main.py show-latest` |
| `show-latest --details` | View with full rationales | `python src/app/main.py show-latest --details` |
| `journal` | Log trade decision | `python src/app/main.py journal` |
| `report` | View statistics | `python src/app/main.py report` |
| `loop` | Run analysis in a loop | `python src/app/main.py loop --symbol EURUSD --timeframe 1h` |

</details>

---

### Symbol Analysis

Run full symbol analysis:

```bash
python src/app/main.py analyze --symbol EURUSD --timeframe 1h
```

**Parameters:**
- `--symbol` (required) — trading symbol (e.g., EURUSD, GBPUSD)
- `--timeframe` (optional) — timeframe (1m, 5m, 15m, 1h, 1d). Default: 1h
- `--verbose` (optional) — show detailed analysis output during execution (technical analysis, news, synthesis)

**Examples:**

```bash
# Analyze EURUSD on hourly timeframe
python src/app/main.py analyze --symbol EURUSD --timeframe 1h

# Analyze GBPUSD on 15-minute timeframe
python src/app/main.py analyze --symbol GBPUSD --timeframe 15m

# Analyze USDJPY on daily timeframe
python src/app/main.py analyze --symbol USDJPY --timeframe 1d

# Analyze with detailed output
python src/app/main.py analyze --symbol EURUSD --timeframe 1h --verbose
```

**Checking Artifacts:**

After running analysis, artifacts are saved in `artifacts/run_{run_id}/`:
- `recommendation.json` — JSON with recommendation data
- `rationales.md` — Markdown file with all rationales (Technical, News, Synthesis)
- `llm/` — Directory containing LLM exchange artifacts:
  - `llm/tech_analysis/` — Technical analysis request/response
  - `llm/news_analysis/` — News analysis request/response
  - `llm/synthesis/` — Synthesis request/response
  - `llm/verification/` — Verification request/response (if enabled)
  - Each task directory contains `request.json`, `response.json`, and `response.txt`

To view artifacts:
```bash
# List all run directories
ls artifacts/

# View recommendation for a specific run
cat artifacts/run_123/recommendation.json

# View rationales for a specific run
cat artifacts/run_123/rationales.md

# View LLM exchange for technical analysis
cat artifacts/run_123/llm/tech_analysis/response.json
```

**--verbose mode:**
When using the `--verbose` flag, the system displays detailed information at each stage:
- **Technical Rationale** — full text of technical analysis from LLM
- **News Digest** — aggregated news context
- **Synthesis Logic** — recommendation synthesis logic with action, confidence, and brief rationale

If the text is too long (more than 2000 characters), it will be truncated with a hint to use `show-latest --details` to view the full text.

**What happens:**

<details>
<summary><strong>📊 Detailed Analysis Pipeline</strong></summary>

1. **Market Data Retrieval** 📈
   - Fetches historical candles from OANDA or Twelve Data
   - Validates data quality and completeness
   - Applies fallback logic if primary provider fails

2. **Technical Indicator Calculation** 🔢
   - Calculates RSI, MACD, Bollinger Bands, etc.
   - Computes volatility metrics
   - Detects market regime (trend/flat)

3. **Technical Analysis via LLM** 🤖
   - Sends feature snapshot to LLM
   - Receives technical rationale
   - Analyzes chart patterns and indicators

4. **News Context Retrieval** 📰
   - Fetches relevant news from GDELT/NewsAPI
   - Aggregates and filters news articles
   - Generates news digest with sentiment

5. **Final Recommendation Synthesis** 🎯
   - Combines technical and fundamental analysis
   - Generates action (CALL/PUT/HOLD)
   - Assigns confidence level (0.0-1.0)

6. **Save to Database** 💾
   - Persists recommendation
   - Saves all rationales
   - Links to analysis run metadata

</details>

### View Latest Recommendation

```bash
python src/app/main.py show-latest
```

Or with detailed information:

```bash
python src/app/main.py show-latest --details
```

**Without --details flag:**
Displays the last saved recommendation with color coding:
- 🟢 Green — CALL (buy)
- 🔴 Red — PUT (sell)
- 🟡 Yellow — other actions

Confidence is also color-coded:
- 🟢 Green — high confidence (≥70%)
- 🟡 Yellow — medium confidence (50-70%)
- 🔴 Red — low confidence (<50%)

**With --details flag:**
After the recommendation table, displays saved rationales from the database:
- **Technical Analysis** — technical analysis performed by LLM (includes LLM metadata: provider, model, latency, attempts)
- **News Context** — news context used in analysis (includes LLM metadata if available)
- **AI Synthesis** — final recommendation rationale (includes LLM metadata)
- **Verification Report** — if verification is enabled, shows verification results with issues and suggested fixes

LLM metadata includes:
- Provider name (e.g., `ollama_local`, `deepseek_api`)
- Model name (e.g., `llama3:latest`, `deepseek-chat`)
- Latency in milliseconds
- Number of attempts (if fallback was used)
- Error message (if any)

If the recommendation doesn't have a `run_id` (old entries created before the run tracking system was implemented), an appropriate message is displayed.

### Trade Journal

Interactive command for logging trading decisions:

```bash
python src/app/main.py journal
```

The command:
1. Shows the latest recommendation
2. Asks if a trade was opened
3. If no — records skip reason
4. If yes — records outcome (WIN/LOSS/DRAW) and comment

**Example session:**

```
Latest Recommendation:
  Symbol: EURUSD
  Action: CALL
  Timeframe: 1h
  Timestamp: 2024-01-15 10:30:00

Did you take this trade? [y/N]: y
What was the result? [WIN/LOSS/DRAW]: WIN
How did you feel about the trade? [Confident/Nervous/Lucky]: Confident
Trade logged. Outcome ID: 42
```

### Statistics Report

View trading statistics:

```bash
python src/app/main.py report
```

Displays a table with statistics for each symbol:
- Total trades
- Win rate percentage
- Number of wins, losses, draws
- Number of skipped trades

Additionally, shows news statistics table with:
- News quality distribution (HIGH, MEDIUM, LOW)
- Provider usage statistics
- News sentiment analysis

### Automated Loop

Run analysis continuously in a loop:

```bash
python src/app/main.py loop --symbol EURUSD --timeframe 1h
```

**Parameters:**
- `--symbol` (required) — trading symbol (e.g., EURUSD, GBPUSD)
- `--timeframe` (optional) — timeframe (1m, 5m, 15m, 1h, 1d). Default: 1h
- `--interval-seconds` (optional) — interval between iterations in seconds. Default: 60.0
- `--iterations` (optional) — maximum number of iterations (runs indefinitely if not set)

**How it works:**
- Uses `MinuteLoop` to run analysis on minute boundaries
- Uses `Scheduler` to determine when to run analysis for each symbol
- Automatically aligns with minute boundaries (e.g., runs at :00, :01, :02, etc.)
- Can be interrupted with Ctrl+C

**Examples:**

```bash
# Run loop for EURUSD on hourly timeframe
python src/app/main.py loop --symbol EURUSD --timeframe 1h

# Run loop with custom interval (every 2 minutes)
python src/app/main.py loop --symbol GBPUSD --timeframe 1h --interval-seconds 120

# Run loop for limited iterations (10 times)
python src/app/main.py loop --symbol USDJPY --timeframe 1d --iterations 10
```

**Note:** The loop uses the scheduler to determine when analysis should run. For MVP, the scheduler allows runs at any time, but the loop aligns execution with minute boundaries.

## Workflow

<details>
<summary><strong>🎬 Interactive Workflow Diagram</strong></summary>

```
┌─────────────────┐
│  Start Analysis │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Fetch Market   │
│     Data        │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Calculate       │
│  Indicators     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  LLM Analysis   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Fetch News     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Synthesize     │
│ Recommendation  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Save to DB     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ View & Decide   │
└─────────────────┘
```

</details>

---

### Typical Usage Scenario

1. **Run analysis:**
   ```bash
   python src/app/main.py analyze --symbol EURUSD --timeframe 1h
   ```

2. **View recommendation:**
   ```bash
   python src/app/main.py show-latest
   ```

3. **Make decision:**
   - Review recommendation and rationale
   - Make decision on trade entry
   - Execute trade on broker (manually)

4. **Log outcome:**
   ```bash
   python src/app/main.py journal
   ```

5. **Analyze statistics:**
   ```bash
   python src/app/main.py report
   ```

### Automation

<details>
<summary><strong>⏰ Automated Scheduling Options</strong></summary>

#### Linux/macOS (cron)

```bash
# Edit crontab
crontab -e

# Run every hour
0 * * * * cd /path/to/project && /usr/bin/python3 src/app/main.py analyze --symbol EURUSD --timeframe 1h >> /var/log/trading_assistant.log 2>&1

# Run every 4 hours
0 */4 * * * cd /path/to/project && /usr/bin/python3 src/app/main.py analyze --symbol GBPUSD --timeframe 1h

# Run daily at 9 AM
0 9 * * * cd /path/to/project && /usr/bin/python3 src/app/main.py analyze --symbol USDJPY --timeframe 1d
```

#### Windows (Task Scheduler)

1. Open Task Scheduler
2. Create Basic Task
3. Set trigger (Daily, Weekly, etc.)
4. Set action: `python src/app/main.py analyze --symbol EURUSD --timeframe 1h`
5. Set working directory to project root

#### Systemd Service (Linux)

Create `/etc/systemd/system/trading-assistant.service`:

```ini
[Unit]
Description=Trading Research Assistant
After=network.target

[Service]
Type=oneshot
User=your_user
WorkingDirectory=/path/to/project
ExecStart=/usr/bin/python3 src/app/main.py analyze --symbol EURUSD --timeframe 1h
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

Then create a timer:

```ini
[Unit]
Description=Run Trading Assistant Hourly

[Timer]
OnCalendar=hourly
Persistent=true

[Install]
WantedBy=timers.target
```

</details>

## Utility Scripts

The project includes utility scripts in `scripts/python/`:

### Model Management

**Download models from routing configuration:**
```bash
python scripts/python/download_models.py --from-routing
```

**Download specific models:**
```bash
# Download Hugging Face model
python scripts/python/download_models.py --hf-model Qwen/Qwen2.5-7B-Instruct

# Pull Ollama model
python scripts/python/download_models.py --ollama-model qwen2.5:7b

# Prefetch HF models in Ollama after download
python scripts/python/download_models.py --from-routing --prefetch-ollama
```

### System Profiling

**Check GPU and RAM:**
```bash
python scripts/python/check_gpu.py
```

This script shows:
- System RAM (total, available, used)
- GPU VRAM (if available)
- Model size recommendations based on available resources

**Check environment:**
```bash
python scripts/python/check_environment.py
```

This script verifies:
- Python version
- Required dependencies
- Environment variables
- Database accessibility
- LLM provider connectivity (Ollama local/server, DeepSeek API)

## Tips and Recommendations

1. **Start with testing**: Use demo account and small amounts to verify the system
2. **Keep a journal**: Regularly log results to analyze effectiveness
3. **Monitor confidence**: Pay attention to confidence level in recommendations
4. **Use multiple timeframes**: Analyze one symbol on different timeframes
5. **Check news**: Consider fundamental analysis when making decisions
6. **Update regularly**: Keep track of system and dependency updates
7. **Configure LLM routing**: Set up task-specific routing for optimal performance
8. **Enable verification**: Use `LLM_VERIFIER_ENABLED=true` for additional safety checks

## Additional Information

<details>
<summary><strong>📚 Related Documentation</strong></summary>

- [Project Architecture](./architecture.md) - Detailed architecture documentation
- [Import Rules](./import_rules.md) - Module dependency rules
- [Safety Policy](./safety_policy.md) - Risk management policies
- [Troubleshooting Guide](./troubleshooting.md) - Common issues and solutions
- [Project Overview](./overview.md) - Project overview and features

</details>

---

[📖 Overview](./overview.md) | [🏗️ Architecture](./architecture.md) | [🔧 Troubleshooting](./troubleshooting.md) | [🔒 Safety Policy](./safety_policy.md)