# Usage Guide

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

# With LLM support
uv sync --extra llm

# With UI support
uv sync --extra ui

# All optional dependencies
uv sync --all-extras

# With dev dependencies
uv sync --extra dev
```

#### Using pip

```bash
# Base dependencies
pip install -e .

# With optional groups
pip install -e ".[llm,ui,dev]"
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

# --- Ollama (LLM) ---
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2

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

### Symbol Analysis

Run full symbol analysis:

```bash
python src/app/main.py analyze --symbol EURUSD --timeframe 1h
```

**Parameters:**
- `--symbol` (required) — trading symbol (e.g., EURUSD, GBPUSD)
- `--timeframe` (optional) — timeframe (1m, 5m, 15m, 30m, 1h, 4h, 1d). Default: 1h
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

**--verbose mode:**
When using the `--verbose` flag, the system displays detailed information at each stage:
- **Technical Rationale** — full text of technical analysis from LLM
- **News Digest** — aggregated news context
- **Synthesis Logic** — recommendation synthesis logic with action, confidence, and brief rationale

If the text is too long (more than 2000 characters), it will be truncated with a hint to use `show-latest --details` to view the full text.

**What happens:**
1. Market data retrieval (candles)
2. Technical indicator calculation
3. Technical analysis via LLM
4. News context retrieval
5. Final recommendation synthesis
6. Save to database

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
- **Technical Analysis** — technical analysis performed by LLM
- **News Context** — news context used in analysis
- **AI Synthesis** — final recommendation rationale

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

## Workflow

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

For automatic analysis runs, you can use cron (Linux/Mac) or Task Scheduler (Windows):

```bash
# Every hour
0 * * * * cd /path/to/project && python src/app/main.py analyze --symbol EURUSD --timeframe 1h
```

## Troubleshooting

### Error: "No market data provider configured"

**Cause**: API keys for data providers are not configured.

**Solution**: Set `OANDA_API_KEY` or `TWELVE_DATA_API_KEY` in `.env` file.

### Error: "OLLAMA_MODEL must be set"

**Cause**: Ollama model is not specified.

**Solution**: Set `OLLAMA_MODEL` in `.env` file and ensure Ollama is running.

### Error: "Insufficient candles: got X, need at least 200"

**Cause**: Insufficient historical data.

**Solution**: 
- Check data availability from provider
- Ensure symbol is correct
- Try a different timeframe

### Ollama Connection Error

**Cause**: Ollama is not running or not accessible.

**Solution**:
1. Ensure Ollama is running: `ollama serve`
2. Check `OLLAMA_BASE_URL` in `.env`
3. For remote server, ensure network accessibility

### Database Locked

**Cause**: Another application is using the SQLite database.

**Solution**: Close other application instances or other programs using the database.

## Tips and Recommendations

1. **Start with testing**: Use demo account and small amounts to verify the system
2. **Keep a journal**: Regularly log results to analyze effectiveness
3. **Monitor confidence**: Pay attention to confidence level in recommendations
4. **Use multiple timeframes**: Analyze one symbol on different timeframes
5. **Check news**: Consider fundamental analysis when making decisions
6. **Update regularly**: Keep track of system and dependency updates

## Additional Information

- [Project Architecture](architecture.md)
- [Import Rules](import_rules.md)
- [Safety Policy](safety_policy.md)