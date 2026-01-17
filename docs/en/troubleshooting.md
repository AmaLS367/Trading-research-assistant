# 🔧 Troubleshooting Guide

**Common issues and solutions**

[![Support](https://img.shields.io/badge/Support-Troubleshooting-FF6B6B)](./troubleshooting.md)
[![Status](https://img.shields.io/badge/Status-Active-success)](./troubleshooting.md)

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
- [Configuration and Environment Variable Issues](#-configuration-and-environment-variable-issues)
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

2. **Copy `.env.example` to `.env`** if missing:
   ```bash
   cp .env.example .env  # Linux/macOS
   Copy-Item .env.example .env  # Windows (PowerShell)
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

## 🔧 Configuration and Environment Variable Issues

### Problem: Timeout at 60 seconds for Ollama

**Symptoms:**
```
Provider response failed: task=news_analysis, provider=ollama_local, model=qwen2.5:7b, timeout_seconds=60.0, attempt=1, elapsed_ms=62000, error=timed out
Provider timeout: timeout_seconds=60.0
```

**Cause:** Default timeout is too short for local Ollama models, especially for `news_analysis`, `synthesis`, and `verification` tasks.

**Solutions:**

<details>
<summary><strong>Step-by-step fix</strong></summary>

1. **Check current timeout settings:**
   ```bash
   python -c "from src.app.settings import settings; print(f'OLLAMA_LOCAL_TIMEOUT_SECONDS: {settings.ollama_local_timeout_seconds}')"
   ```

2. **Increase timeout for specific task in `.env`:**
   ```bash
   # For news_analysis (recommended 240 seconds)
   OLLAMA_LOCAL_NEWS_TIMEOUT_SECONDS=240.0
   
   # For synthesis (recommended 240 seconds)
   OLLAMA_LOCAL_SYNTHESIS_TIMEOUT_SECONDS=240.0
   
   # For verification (recommended 240 seconds)
   OLLAMA_LOCAL_VERIFIER_TIMEOUT_SECONDS=240.0
   
   # For tech_analysis (recommended 120 seconds)
   OLLAMA_LOCAL_TECH_TIMEOUT_SECONDS=120.0
   ```

3. **Or set general timeout for ollama_local:**
   ```bash
   OLLAMA_LOCAL_TIMEOUT_SECONDS=240.0
   ```

4. **Check timeout priority:**
   - Priority 1: `OLLAMA_LOCAL_{TASK}_TIMEOUT_SECONDS` (highest)
   - Priority 2: `OLLAMA_LOCAL_TIMEOUT_SECONDS`
   - Priority 3: `{TASK}_TIMEOUT_SECONDS` (e.g., `NEWS_TIMEOUT_SECONDS`)
   - Priority 4: `LLM_TIMEOUT_SECONDS` (global, default 60.0)

5. **Restart application** after changing `.env`

</details>

**Diagnostics:**
- Check logs for `timeout_seconds=60.0` for tasks that should use Ollama
- Ensure model is not overloaded by other processes
- Check VRAM usage: `nvidia-smi` (if using GPU)

---

### Problem: Model not found (model not found)

**Symptoms:**
```
Provider response failed: task=news_analysis, provider=ollama_local, model=qwen2.5:7b, error=model not found
ollama: model 'qwen2.5:7b' not found, try pulling it first
Error: model 'qwen2.5:7b' not found
```

**Cause:** Model is not loaded in Ollama or incorrect model name is specified.

**Solutions:**

<details>
<summary><strong>Step-by-step fix</strong></summary>

1. **Check list of available models:**
   ```bash
   ollama list
   ```

2. **Check model name in `.env`:**
   ```bash
   # For local branch
   NEWS_LOCAL_PRIMARY_MODEL=qwen2.5:7b
   
   # Ensure name exactly matches what `ollama list` shows
   ```

3. **Load model manually:**
   ```bash
   ollama pull qwen2.5:7b
   ```

4. **Or use automatic download:**
   ```bash
   python -m scripts.python.download_models --from-routing
   ```

5. **Verify model accessibility:**
   ```bash
   ollama run qwen2.5:7b "test"
   ```

6. **If model not found on Hugging Face:**
   - Check that model exists: https://huggingface.co/models
   - For gated models, set `HF_TOKEN` in `.env`
   - Check internet connection

</details>

**Prevention:**
- Use `python -m scripts.python.download_models --from-routing` before first run
- Check preflight logs for model download errors
- Ensure `HUGGINGFACE_HUB_CACHE` points to accessible directory

---

### Problem: Provider unavailable (provider unavailable)

**Symptoms:**
```
Provider unavailable, skipping: provider=deepseek_api
Provider health check failed: provider=deepseek_api, error=API key not set
```

**Cause:** API key is not set, invalid, or provider is unavailable.

**Solutions:**

<details>
<summary><strong>Diagnostics and fix</strong></summary>

1. **Check API key presence in `.env`:**
   ```bash
   # For DeepSeek
   DEEPSEEK_API_KEY=your_api_key_here
   ```

2. **Check key validity:**
   ```bash
   python -c "from src.app.settings import settings; print('DeepSeek key set:', bool(settings.deepseek_api_key))"
   ```

3. **Check health check in logs:**
   - Look for `Provider health check` lines in startup logs
   - Verify provider is marked as `available=True`

4. **For DeepSeek API:**
   - Get key at https://platform.deepseek.com/
   - Ensure key has API usage permissions
   - Check account balance

5. **For Ollama Server:**
   - Check that `OLLAMA_SERVER_URL` is accessible
   - Ensure URL is not `localhost` or `127.0.0.1` (for server branch)
   - Verify server is running: `curl http://your-server:11434/api/tags`

</details>

**Diagnostics:**
- Check preflight logs for health check errors
- Ensure environment variables are loaded before application startup
- Check network accessibility for remote providers

---

### Problem: OLLAMA_SERVER_URL not working

**Symptoms:**
```
ConnectionRefusedError: [Errno 111] Connection refused
httpx.ConnectTimeout: Connection timeout
Provider response failed: provider=ollama_server, error=Connection refused
```

**Cause:** Ollama server is unavailable, incorrect URL, or server is not running.

**Solutions:**

<details>
<summary><strong>Step-by-step fix</strong></summary>

1. **Check `OLLAMA_SERVER_URL` value in `.env`:**
   ```bash
   OLLAMA_SERVER_URL=http://your-server-ip:11434
   # DO NOT use localhost or 127.0.0.1 for server branch
   ```

2. **Check server accessibility:**
   ```bash
   # Ping check
   ping your-server-ip
   
   # HTTP endpoint check
   curl http://your-server-ip:11434/api/tags
   ```

3. **Check firewall and network rules:**
   - Ensure port 11434 is open
   - For AWS/GCP: check security groups
   - For corporate networks: check proxy settings

4. **Verify server is running:**
   ```bash
   # On server
   ollama serve
   # or check systemd service
   systemctl status ollama
   ```

5. **Check Ollama server logs:**
   - On server, check logs for errors
   - Ensure server is listening on correct interface

</details>

**Prevention:**
- Use health check before running analysis
- Set up monitoring for server availability
- Use fallback providers

---

### Problem: All providers fail, last resort used

**Symptoms:**
```
All configured providers failed, trying last resort
Provider response failed: task=news_analysis, provider=ollama_local, error=...
Provider response failed: task=news_analysis, provider=deepseek_api, error=...
Switching to last resort: provider=ollama_local, model=llama3:latest
```

**Cause:** All configured providers are unavailable or failing with errors.

**Solutions:**

<details>
<summary><strong>Diagnostics and fix</strong></summary>

1. **Check last resort configuration in `.env`:**
   ```bash
   LLM_LAST_RESORT_PROVIDER=ollama_local
   LLM_LAST_RESORT_MODEL=llama3:latest
   OLLAMA_LOCAL_URL=http://localhost:11434
   ```

2. **Verify Ollama is running locally:**
   ```bash
   curl http://localhost:11434/api/tags
   ```

3. **Verify `llama3:latest` model is loaded:**
   ```bash
   ollama list | grep llama3
   # If not, load it:
   ollama pull llama3:latest
   ```

4. **Check logs for provider failure reasons:**
   - Look for specific errors for each provider
   - Check timeouts (see "Timeout at 60 seconds" problem)
   - Check API key availability

5. **Temporary solution:**
   - Use only `ollama_local` for all tasks
   - Ensure all required models are loaded
   - Increase timeouts for local models

</details>

**Prevention:**
- Configure multiple fallback providers for each task
- Regularly check health check of all providers
- Monitor logs for early signs of problems

---

### Problem: RUNTIME_ENV does not switch branch

**Symptoms:**
- Providers from `local` branch are used, even though `RUNTIME_ENV=server` is set
- Or vice versa: providers from `server` are used, even though `RUNTIME_ENV=local` is set

**Cause:** Environment variable is not loaded or set after application startup.

**Solutions:**

<details>
<summary><strong>Step-by-step fix</strong></summary>

1. **Check `RUNTIME_ENV` value in `.env`:**
   ```bash
   RUNTIME_ENV=local  # or server
   ```

2. **Ensure variable is set BEFORE application startup:**
   ```bash
   # Correct: set in .env and restart
   # Incorrect: export in terminal after startup
   ```

3. **Check current value in runtime:**
   ```bash
   python -c "from src.app.settings import settings; print(f'RUNTIME_ENV: {settings.runtime_env}')"
   ```

4. **Check logs for branch selection:**
   - Look for lines `Using routing branch: local` or `Using routing branch: server`
   - Verify correct branch is used

5. **Restart application** after changing `RUNTIME_ENV`

</details>

**Diagnostics:**
- Check preflight logs for branch selection
- Ensure `.env` file is loaded correctly
- Check for conflicting environment variables in system

---

### Problem: HF models not downloading

**Symptoms:**
```
Error downloading model from Hugging Face: model_id=..., error=...
HTTP 401: Unauthorized
HTTP 403: Forbidden
Connection timeout
```

**Cause:** Issues with Hugging Face access, missing token for gated models, or network problems.

**Solutions:**

<details>
<summary><strong>Step-by-step fix</strong></summary>

1. **Check `HF_TOKEN` for gated models:**
   ```bash
   HF_TOKEN=hf_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   ```
   - Get token at https://huggingface.co/settings/tokens
   - Ensure token has `read` permissions

2. **Check cache path:**
   ```bash
   HUGGINGFACE_HUB_CACHE=models/.cache
   # Ensure path exists and is writable
   ```

3. **Check internet availability:**
   ```bash
   curl https://huggingface.co
   ```

4. **Check available disk space:**
   - Some models take 10+ GB
   - Ensure sufficient disk space

5. **Try downloading model manually:**
   ```bash
   python -c "from huggingface_hub import snapshot_download; snapshot_download(repo_id='your-model-id', cache_dir='models/.cache')"
   ```

6. **Check preflight logs:**
   - Look for specific errors when downloading models
   - Verify model exists on Hugging Face

</details>

**Prevention:**
- Download models in advance via `download_models`
- Use local cache for offline work
- Regularly check model availability on Hugging Face

---

### Problem: Progress bars not showing

**Symptoms:**
- No progress indicator during model download
- Download happens "silently"

**Cause:** Environment variables disable progress bars.

**Solutions:**

<details>
<summary><strong>Step-by-step fix</strong></summary>

1. **Check variables in `.env`:**
   ```bash
   # Ensure these variables are NOT set or empty:
   # HF_HUB_DISABLE_PROGRESS_BARS=
   # TQDM_DISABLE=
   ```

2. **Or explicitly disable them:**
   ```bash
   HF_HUB_DISABLE_PROGRESS_BARS=
   TQDM_DISABLE=
   ```

3. **Check that variables are not set in system:**
   ```bash
   # Windows PowerShell
   $env:HF_HUB_DISABLE_PROGRESS_BARS
   $env:TQDM_DISABLE
   
   # If set, remove or set to empty string
   ```

4. **Restart application** after changing variables

</details>

**Diagnostics:**
- Check logs for model download messages
- Ensure terminal supports ANSI escape codes
- Check that output is not redirected to file

---

### Problem: Cache taking too much space

**Symptoms:**
- Directory `models/.cache` or `HUGGINGFACE_HUB_CACHE` takes too much space (10+ GB)
- Insufficient disk space

**Cause:** Cache accumulated downloaded models and their versions.

**Solutions:**

<details>
<summary><strong>Cache cleanup</strong></summary>

1. **Check cache size:**
   ```bash
   # Windows PowerShell
   Get-ChildItem -Path models\.cache -Recurse | Measure-Object -Property Length -Sum
   
   # Linux/macOS
   du -sh models/.cache
   ```

2. **Delete unused models:**
   ```bash
   # Delete entire cache directory (careful: deletes all models)
   Remove-Item -Recurse -Force models\.cache  # Windows
   rm -rf models/.cache  # Linux/macOS
   ```

3. **Or delete specific models:**
   - Find model directories in `models/.cache/huggingface/hub/`
   - Delete only unused models

4. **Configure different cache path:**
   ```bash
   HUGGINGFACE_HUB_CACHE=/path/to/larger/disk/.cache
   ```

5. **Use symlinks to save space:**
   - Create cache on different disk
   - Create symlink in `models/.cache`

</details>

**Prevention:**
- Regularly clean unused models
- Use separate disk for model cache
- Monitor cache size

---

### Problem: API keys visible in logs

**Symptoms:**
- Full API keys visible in logs
- Secret data appears in logs

**Cause:** Auth masking is disabled or not working.

**Solutions:**

<details>
<summary><strong>Step-by-step fix</strong></summary>

1. **Enable masking in `.env`:**
   ```bash
   LOG_MASK_AUTH=true
   ```

2. **Verify masking works:**
   ```bash
   python -c "from src.app.settings import settings; print(f'LOG_MASK_AUTH: {settings.log_mask_auth}')"
   ```

3. **Restart application** after changing

4. **Check logs:**
   - API keys should be masked as `***` or `[MASKED]`
   - If still visible, check logging code

5. **If problem persists:**
   - Verify `LOG_MASK_AUTH` is loaded from `.env`
   - Ensure no conflicting environment variables
   - Check code version (masking may not be implemented for all providers)

</details>

**Prevention:**
- Always use `LOG_MASK_AUTH=true` in production
- Do not commit logs with secrets to git
- Regularly rotate API keys

---

### Problem: Switching to fallback too often

**Symptoms:**
```
Switching to fallback: reason=timeout, next_provider=ollama_local, next_model=llama3:latest
Switching to fallback: reason=error: Connection refused, next_provider=deepseek_api, next_model=deepseek-chat
Provider response failed: task=news_analysis, provider=ollama_local, error=...
```

**Cause:** Primary provider regularly fails or doesn't respond in time, system constantly switches to fallback.

**Solutions:**

<details>
<summary><strong>Diagnostics and fix</strong></summary>

1. **Check reason in logs:**
   - Look for lines `Switching to fallback: reason=...`
   - Determine main cause: `timeout`, `error: Connection refused`, `error: model not found`, etc.

2. **If reason is timeout:**
   - Increase timeouts for primary provider:
     ```bash
     OLLAMA_LOCAL_NEWS_TIMEOUT_SECONDS=300.0
     OLLAMA_LOCAL_SYNTHESIS_TIMEOUT_SECONDS=300.0
     ```
   - Check that model is not overloaded by other processes
   - Check VRAM usage: `nvidia-smi` (if using GPU)

3. **If reason is Connection refused:**
   - Check that Ollama is running: `ollama list`
   - Check `OLLAMA_LOCAL_URL` or `OLLAMA_SERVER_URL` in `.env`
   - Check server accessibility: `curl http://your-server:11434/api/tags`

4. **If reason is model not found:**
   - Load model: `ollama pull qwen2.5:7b`
   - Or use script: `python -m scripts.python.download_models --from-routing --profile small`
   - Check model name in `.env`: must exactly match `ollama list`

5. **If reason is provider unavailable:**
   - Check health check in logs: `Health check: provider=..., available=false`
   - Check API keys: `DEEPSEEK_API_KEY`, `OLLAMA_SERVER_URL`, etc.
   - Check account balance for paid APIs

6. **Configuration optimization:**
   - If primary provider constantly fails, consider switching primary to more reliable one
   - For example, if `ollama_local` constantly times out, use `deepseek_api` as primary
   - Or switch task to server branch: `RUNTIME_ENV=server`

7. **Monitoring:**
   - Regularly check logs for fallback switch frequency
   - Set up alerts for frequent fallback switches
   - Analyze patterns: which tasks switch most often

</details>

**Diagnostics:**
- Count number of `Switching to fallback` in logs per session
- Determine which tasks switch most often
- Verify that primary provider is actually unavailable or just slow

**Prevention:**
- Configure correct timeouts for each provider and task
- Use health check before running analysis
- Regularly check availability of all providers
- Monitor performance of primary providers

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
   - [Roadmap](./roadmap.md)

3. **Create issue report:**
   - Include error messages
   - System information
   - Configuration (without secrets)
   - Steps to reproduce

---

[📖 Overview](./overview.md) | [📚 Usage Guide](./usage_guide.md) | [🏗️ Architecture](./architecture.md) | [🗺️ Roadmap](./roadmap.md)
