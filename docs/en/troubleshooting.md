<div align="center">

# 🔧 Troubleshooting Guide

**Common issues and solutions**

[![Support](https://img.shields.io/badge/Support-Troubleshooting-FF6B6B)](./troubleshooting.md)
[![Status](https://img.shields.io/badge/Status-Active-success)](./troubleshooting.md)

</div>

---

## 📋 Table of Contents

<details>
<summary>Click to expand</summary>

- [Installation Issues](#-installation-issues)
- [Configuration Problems](#-configuration-problems)
- [API Connection Errors](#-api-connection-errors)
- [LLM/Ollama Issues](#-llmollama-issues)
- [Database Problems](#-database-problems)
- [Data Retrieval Issues](#-data-retrieval-issues)
- [Performance Issues](#-performance-issues)
- [General Tips](#-general-tips)

</details>

---

## 🚀 Installation Issues

### Problem: `uv` command not found

**Symptoms:**
```bash
$ uv sync
bash: uv: command not found
```

**Solutions:**

<details>
<summary><strong>Windows</strong></summary>

1. Install using PowerShell:
   ```powershell
   powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
   ```

2. Restart your terminal or add to PATH manually

3. Verify installation:
   ```bash
   uv --version
   ```

</details>

<details>
<summary><strong>Linux/macOS</strong></summary>

1. Install using curl:
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. Add to PATH (if needed):
   ```bash
   export PATH="$HOME/.cargo/bin:$PATH"
   ```

3. Verify installation:
   ```bash
   uv --version
   ```

</details>

---

### Problem: Python version mismatch

**Symptoms:**
```
Error: requires-python = ">=3.11"
```

**Solutions:**

1. **Check Python version:**
   ```bash
   python --version
   ```

2. **Install Python 3.11+** if needed:
   - Windows: Download from [python.org](https://www.python.org/downloads/)
   - Linux: `sudo apt install python3.11` (Ubuntu/Debian)
   - macOS: `brew install python@3.11`

3. **Use specific Python version with uv:**
   ```bash
   uv python install 3.11
   uv sync --python 3.11
   ```

---

## ⚙️ Configuration Problems

### Error: "No market data provider configured"

**Symptoms:**
```
RuntimeError: No market data provider configured
```

**Cause:** API keys for data providers are not configured.

**Solutions:**

<details>
<summary><strong>Step-by-step fix</strong></summary>

1. **Check `.env` file exists:**
   ```bash
   ls -la .env  # Linux/macOS
   dir .env     # Windows
   ```

2. **Create `.env` file** if missing:
   ```bash
   touch .env  # Linux/macOS
   type nul > .env  # Windows
   ```

3. **Add required API keys:**
   ```bash
   # OANDA (primary)
   OANDA_API_KEY=your_oanda_api_key_here
   OANDA_BASE_URL=https://api-fxpractice.oanda.com
   
   # OR Twelve Data (fallback)
   TWELVE_DATA_API_KEY=your_twelve_data_key
   TWELVE_DATA_BASE_URL=https://api.twelvedata.com
   ```

4. **Verify configuration:**
   ```bash
   python -c "from src.app.settings import settings; print(settings.oanda_api_key[:10] if settings.oanda_api_key else 'Not set')"
   ```

</details>

**Prevention:**
- Always use `.env` file (never commit it to git)
- Test API keys before running analysis
- Use fallback providers for redundancy

---

### Error: "OLLAMA_MODEL must be set"

**Symptoms:**
```
ValueError: OLLAMA_MODEL must be set
```

**Cause:** Ollama model is not specified in environment variables.

**Solutions:**

1. **Set model in `.env`:**
   ```bash
   OLLAMA_MODEL=llama3.2
   # or
   OLLAMA_MODEL=llama3.1
   # or any other model you have
   ```

2. **List available models:**
   ```bash
   ollama list
   ```

3. **Pull model if missing:**
   ```bash
   ollama pull llama3.2
   ```

4. **Verify model is accessible:**
   ```bash
   ollama run llama3.2 "Hello"
   ```

---

## 🌐 API Connection Errors

### Problem: OANDA API connection timeout

**Symptoms:**
```
httpx.ConnectTimeout: Connection timeout
```

**Solutions:**

<details>
<summary><strong>Diagnostic steps</strong></summary>

1. **Test API connectivity:**
   ```bash
   curl -H "Authorization: Bearer YOUR_API_KEY" https://api-fxpractice.oanda.com/v3/accounts
   ```

2. **Check firewall/proxy settings:**
   - Ensure port 443 (HTTPS) is open
   - Configure proxy if behind corporate firewall

3. **Verify API key permissions:**
   - Check OANDA account settings
   - Ensure API key has read permissions

4. **Try fallback provider:**
   - Set `TWELVE_DATA_API_KEY` in `.env`
   - System will automatically fallback

</details>

**Common causes:**
- Network connectivity issues
- Incorrect API endpoint URL
- Expired or invalid API key
- Rate limiting (too many requests)

---

### Problem: GDELT API rate limiting

**Symptoms:**
```
HTTP 429: Too Many Requests
```

**Solutions:**

1. **Implement delays between requests:**
   ```python
   # Already handled in code, but you can adjust:
   RUNTIME_NEWS_REFRESH_INTERVAL_SECONDS=600  # Increase to 10 minutes
   ```

2. **Use NewsAPI as fallback:**
   ```bash
   NEWSAPI_API_KEY=your_newsapi_key
   ```

3. **Reduce news query frequency:**
   - Only fetch news when needed
   - Cache news results

---

## 🤖 LLM/Ollama Issues

### Problem: Ollama connection refused

**Symptoms:**
```
ConnectionRefusedError: [Errno 111] Connection refused
```

**Solutions:**

<details>
<summary><strong>Local Ollama</strong></summary>

1. **Start Ollama service:**
   ```bash
   ollama serve
   ```

2. **Verify service is running:**
   ```bash
   curl http://localhost:11434/api/tags
   ```

3. **Check `.env` configuration:**
   ```bash
   OLLAMA_BASE_URL=http://localhost:11434
   ```

</details>

<details>
<summary><strong>Remote Ollama</strong></summary>

1. **Verify network connectivity:**
   ```bash
   ping your-ollama-server.com
   curl http://your-ollama-server.com:11434/api/tags
   ```

2. **Check firewall rules:**
   - Ensure port 11434 is open
   - Check security group settings (AWS/GCP)

3. **Update `.env`:**
   ```bash
   OLLAMA_BASE_URL=http://your-ollama-server.com:11434
   ```

4. **Test connection:**
   ```bash
   python -c "import httpx; print(httpx.get('http://your-ollama-server.com:11434/api/tags').json())"
   ```

</details>

---

### Problem: LLM model not found

**Symptoms:**
```
Error: model 'llama3.2' not found
```

**Solutions:**

1. **List available models:**
   ```bash
   ollama list
   ```

2. **Pull the model:**
   ```bash
   ollama pull llama3.2
   ```

3. **Check model name in `.env`:**
   ```bash
   OLLAMA_MODEL=llama3.2  # Must match exact name
   ```

4. **Verify model:**
   ```bash
   ollama run llama3.2 "test"
   ```

---

### Problem: LLM responses are slow

**Symptoms:**
- Analysis takes too long
- Timeout errors

**Solutions:**

1. **Use smaller/faster model:**
   ```bash
   OLLAMA_MODEL=llama3.2:1b  # Smaller quantized version
   ```

2. **Increase timeout settings:**
   ```python
   # In code, adjust LLM timeout if needed
   ```

3. **Use GPU acceleration:**
   ```bash
   # Ensure CUDA/ROCm is available
   ollama run llama3.2 --gpu
   ```

4. **Reduce context window:**
   - Use shorter prompts
   - Limit historical data

---

## 💾 Database Problems

### Problem: Database locked

**Symptoms:**
```
sqlite3.OperationalError: database is locked
```

**Solutions:**

<details>
<summary><strong>Quick fixes</strong></summary>

1. **Close other instances:**
   - Check for multiple Python processes
   - Close database viewers (DB Browser, etc.)

2. **Check for lock files:**
   ```bash
   ls -la db/*.sqlite3-*  # Linux/macOS
   dir db\*.sqlite3-*     # Windows
   ```

3. **Remove lock files** (if safe):
   ```bash
   rm db/*.sqlite3-*  # Linux/macOS
   del db\*.sqlite3-*  # Windows
   ```

</details>

**Prevention:**
- Use connection pooling
- Close database connections properly
- Avoid concurrent writes

---

### Problem: Migration errors

**Symptoms:**
```
sqlite3.OperationalError: table already exists
```

**Solutions:**

1. **Check migration status:**
   ```bash
   sqlite3 db/forex_research_assistant.sqlite3 ".schema"
   ```

2. **Reset database** (⚠️ **WARNING**: Deletes all data):
   ```bash
   rm db/forex_research_assistant.sqlite3  # Linux/macOS
   del db\forex_research_assistant.sqlite3  # Windows
   python src/app/main.py init-db
   ```

3. **Manual migration:**
   ```bash
   sqlite3 db/forex_research_assistant.sqlite3 < src/storage/sqlite/migrations/0001_init.sql
   ```

---

## 📊 Data Retrieval Issues

### Error: "Insufficient candles: got X, need at least 200"

**Symptoms:**
```
ValueError: Insufficient candles: got 150, need at least 200
```

**Cause:** Insufficient historical data from provider.

**Solutions:**

<details>
<summary><strong>Diagnostic checklist</strong></summary>

1. **Verify symbol format:**
   ```bash
   # Correct: EURUSD, GBPUSD, USDJPY
   # Wrong: EUR/USD, EUR-USD
   ```

2. **Check data availability:**
   - OANDA: Verify symbol is tradeable
   - Twelve Data: Check symbol in their database

3. **Try different timeframe:**
   ```bash
   # If 1h fails, try:
   python src/app/main.py analyze --symbol EURUSD --timeframe 1d
   ```

4. **Increase window size** (if needed):
   ```bash
   RUNTIME_MARKET_DATA_WINDOW_CANDLES=150  # Reduce requirement
   ```

5. **Check provider status:**
   - OANDA status page
   - Twelve Data status

</details>

---

### Problem: News data not available

**Symptoms:**
```
No news found for symbol EURUSD
```

**Solutions:**

1. **Check GDELT availability:**
   ```bash
   curl "https://api.gdeltproject.org/api/v2/doc/doc?query=forex%20EURUSD&mode=artlist&format=json"
   ```

2. **Use NewsAPI fallback:**
   ```bash
   NEWSAPI_API_KEY=your_key
   ```

3. **Adjust news query parameters:**
   - Try broader search terms
   - Check date ranges

---

## ⚡ Performance Issues

### Problem: Analysis takes too long

**Symptoms:**
- Analysis runs for > 5 minutes
- System becomes unresponsive

**Solutions:**

1. **Reduce data window:**
   ```bash
   RUNTIME_MARKET_DATA_WINDOW_CANDLES=200  # Instead of 300
   ```

2. **Disable verbose output:**
   ```bash
   # Remove --verbose flag
   python src/app/main.py analyze --symbol EURUSD --timeframe 1h
   ```

3. **Optimize LLM calls:**
   - Use smaller model
   - Reduce prompt size
   - Cache responses

4. **Check system resources:**
   ```bash
   # Monitor CPU/Memory
   top  # Linux/macOS
   taskmgr  # Windows
   ```

---

### Problem: High memory usage

**Symptoms:**
- System runs out of memory
- OOM (Out of Memory) errors

**Solutions:**

1. **Reduce pandas dataframes:**
   - Process data in chunks
   - Clear unused variables

2. **Limit concurrent operations:**
   - Run one analysis at a time
   - Close connections properly

3. **Use data streaming:**
   - Don't load all data at once
   - Process incrementally

---

## 💡 General Tips

### Best Practices

<details>
<summary><strong>Configuration</strong></summary>

- ✅ Always use `.env` file for secrets
- ✅ Test API keys before production use
- ✅ Use fallback providers for redundancy
- ✅ Monitor API rate limits
- ✅ Keep dependencies updated

</details>

<details>
<summary><strong>Development</strong></summary>

- ✅ Use virtual environments
- ✅ Run tests before deployment
- ✅ Check logs regularly
- ✅ Monitor system resources
- ✅ Keep backups of database

</details>

<details>
<summary><strong>Production</strong></summary>

- ✅ Use process managers (systemd, supervisor)
- ✅ Set up logging and monitoring
- ✅ Implement health checks
- ✅ Use connection pooling
- ✅ Schedule regular backups

</details>

---

### Debugging Commands

```bash
# Check configuration
python -c "from src.app.settings import settings; print(settings.model_dump_json(indent=2))"

# Test database connection
python -c "from src.storage.sqlite.connection import DBConnection; db = DBConnection('db/forex_research_assistant.sqlite3'); print('OK')"

# Test API connectivity
python -c "import httpx; print(httpx.get('https://api-fxpractice.oanda.com/v3/accounts', headers={'Authorization': 'Bearer YOUR_KEY'}).status_code)"

# Check Ollama
curl http://localhost:11434/api/tags
```

---

## 🆘 Getting Help

If you're still experiencing issues:

1. **Check logs:**
   - Application logs in `artifacts/`
   - System logs (journalctl, Event Viewer)

2. **Review documentation:**
   - [Usage Guide](./usage_guide.md)
   - [Architecture](./architecture.md)
   - [Safety Policy](./safety_policy.md)

3. **Create issue report:**
   - Include error messages
   - System information
   - Configuration (without secrets)
   - Steps to reproduce

---

<div align="center">

[📖 Overview](./overview.md) • [📚 Usage Guide](./usage_guide.md) • [🏗️ Architecture](./architecture.md)

</div>
