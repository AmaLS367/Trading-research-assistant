# Environment Variables Configuration

## Working with .env.example and .env

Copy `.env.example` to `.env` and fill in the required values. The `.env` file should not be committed to git (already in .gitignore). All variables are read from `.env` at application startup via pydantic-settings.

## Variable Groups

### Application

**APP_ENV**
- What it does: Application environment (development/production)
- When to fill: Always
- Default value: `development`
- How to verify: Environment is visible in logs

**APP_TIMEZONE**
- What it does: Timezone for timestamps
- When to fill: If a different timezone is needed
- Default value: `Asia/Yerevan`
- How to verify: Check timestamps in logs and database

### Market Data Providers

**OANDA_API_KEY**
- What it does: OANDA API key for Forex candles
- When to fill: Required for market data
- How to get: Register on oanda.com, create API token in account settings
- Permissions: Access to practice or live account
- How to verify: Run analysis, check that candles are loaded

**OANDA_ACCOUNT_ID**
- What it does: OANDA account ID
- When to fill: Required together with OANDA_API_KEY
- How to get: In OANDA account settings, Account section
- How to verify: Together with OANDA_API_KEY verification

**OANDA_BASE_URL**
- What it does: OANDA API base URL
- When to fill: Only if using a different endpoint
- Default value: `https://api-fxpractice.oanda.com` (practice)
- How to verify: No verification needed, used automatically

**TWELVE_DATA_API_KEY**
- What it does: Twelve Data API key (fallback candles provider)
- When to fill: Optional, for fallback if OANDA is unavailable
- How to get: Register on twelvedata.com, create API key in Dashboard
- Permissions: Free tier is sufficient for basic use
- How to verify: Should be used automatically if OANDA is unavailable

**TWELVE_DATA_BASE_URL**
- What it does: Twelve Data API base URL
- When to fill: Only if using a different endpoint
- Default value: `https://api.twelvedata.com`
- How to verify: No verification needed

### News Providers

**GDELT_BASE_URL**
- What it does: GDELT API base URL for news
- When to fill: Only if using a different endpoint
- Default value: `https://api.gdeltproject.org`
- How to verify: News should load automatically

**NEWSAPI_API_KEY**
- What it does: NewsAPI API key (optional news provider)
- When to fill: Optional, for additional news sources
- How to get: Register on newsapi.org, create API key in Dashboard
- Permissions: Free tier limited to 100 requests per day
- How to verify: Check news loading logs

**NEWSAPI_BASE_URL**
- What it does: NewsAPI base URL
- When to fill: Only if using a different endpoint
- Default value: `https://newsapi.org`
- How to verify: No verification needed

### Storage

**STORAGE_SQLITE_DB_PATH**
- What it does: Path to SQLite database file
- When to fill: If a different path is needed
- Default value: `db/forex_research_assistant.sqlite3`
- How to verify: Check that file is created at specified path

**STORAGE_ARTIFACTS_DIR**
- What it does: Directory for artifacts (LLM logs, recommendations)
- When to fill: If a different directory is needed
- Default value: `artifacts`
- How to verify: After running analysis, check creation of `artifacts/run_*/`

**STORAGE_MIGRATION_PATH**
- What it does: Path to SQL migrations
- When to fill: Only if migration structure changed
- Default value: `src/storage/sqlite/migrations`
- How to verify: Migrations should be applied on `init-db`

### Runtime

**RUNTIME_MVP_SYMBOLS_RAW**
- What it does: Comma-separated list of symbols for analysis
- When to fill: If different symbols are needed
- Default value: `EURUSD,GBPUSD,USDJPY`
- How to verify: Specified symbols should be processed in logs

**RUNTIME_MVP_TIMEFRAME**
- What it does: Timeframe for analysis (1m, 5m, 15m, 1h, 1d)
- When to fill: If a different timeframe is needed
- Default value: `1m`
- How to verify: Specified timeframe should be used in logs

**RUNTIME_MVP_EXPIRY_SECONDS**
- What it does: Data cache lifetime in seconds
- When to fill: If a different refresh interval is needed
- Default value: `60`
- How to verify: Data should refresh at specified interval

**RUNTIME_LLM_ENABLED**
- What it does: Enable/disable LLM calls
- When to fill: If LLM needs to be disabled for testing
- Default value: `true`
- How to verify: LLM calls should be skipped when `false`

**RUNTIME_LLM_CALL_INTERVAL_SECONDS**
- What it does: Interval between LLM calls in seconds
- When to fill: If a different interval is needed
- Default value: `300`
- How to verify: LLM should be called at specified interval

**RUNTIME_NEWS_REFRESH_INTERVAL_SECONDS**
- What it does: News refresh interval in seconds
- When to fill: If a different interval is needed
- Default value: `300`
- How to verify: News should refresh at specified interval

**RUNTIME_MARKET_DATA_WINDOW_CANDLES**
- What it does: Number of candles for analysis
- When to fill: If different history depth is needed
- Default value: `300`
- How to verify: Specified number of candles should be loaded in logs

**RUNTIME_ENV**
- What it does: Branch selection for LLM routing (local or server)
- When to fill: Required, determines which providers to use
- Default value: `local`
- How to verify: Providers from selected branch should be used in logs

### LLM Router Config

**LLM_ROUTER_MODE**
- What it does: Router mode (sequential or strict)
- When to fill: Only if strict mode is needed (not recommended)
- Default value: `sequential`
- How to verify: Fallback providers should be used with sequential

**LLM_VERIFIER_ENABLED**
- What it does: Enable/disable recommendation verification
- When to fill: If output verification is needed
- Default value: `false`
- How to verify: Verification should run after synthesis when `true`

**LLM_VERIFIER_MODE**
- What it does: Verification mode (soft or hard)
- When to fill: If verification is enabled
- Default value: `soft`
- How to verify: Repair attempts should be made with hard mode

**LLM_VERIFIER_MAX_REPAIRS**
- What it does: Maximum number of repair attempts
- When to fill: If verification is enabled in hard mode
- Default value: `1`
- How to verify: Repair attempts should appear in logs

**LLM_MAX_RETRIES**
- What it does: Maximum number of retry attempts for one provider
- When to fill: If different retry settings are needed
- Default value: `3`
- How to verify: Retry attempts should appear in logs on errors

**LLM_TIMEOUT_SECONDS**
- What it does: Global timeout for all LLM calls
- When to fill: If a different base timeout is needed
- Default value: `60.0`
- How to verify: Specified timeout should be used in logs

**LLM_TEMPERATURE**
- What it does: Global temperature for all LLM calls
- When to fill: If different response creativity is needed
- Default value: `0.2`
- How to verify: Responses should be more/less deterministic

### Per-Task Timeouts

**TECH_TIMEOUT_SECONDS**
- What it does: Timeout for tech_analysis task
- When to fill: If tech_analysis requires more time
- Default value: Uses LLM_TIMEOUT_SECONDS
- How to verify: This timeout should be used for tech_analysis in logs

**NEWS_TIMEOUT_SECONDS**
- What it does: Timeout for news_analysis task
- When to fill: If news_analysis requires more time
- Default value: Uses LLM_TIMEOUT_SECONDS
- How to verify: This timeout should be used for news_analysis in logs

**SYNTHESIS_TIMEOUT_SECONDS**
- What it does: Timeout for synthesis task
- When to fill: If synthesis requires more time
- Default value: Uses LLM_TIMEOUT_SECONDS
- How to verify: This timeout should be used for synthesis in logs

**VERIFIER_TIMEOUT_SECONDS**
- What it does: Timeout for verification task
- When to fill: If verification requires more time
- Default value: Uses LLM_TIMEOUT_SECONDS
- How to verify: This timeout should be used for verification in logs

### Per-Provider Timeouts

**OLLAMA_LOCAL_TIMEOUT_SECONDS**
- What it does: Timeout for all tasks via ollama_local
- When to fill: If ollama_local is slow
- Default value: Uses task timeout
- How to verify: This timeout should be used for ollama_local in logs

**OLLAMA_SERVER_TIMEOUT_SECONDS**
- What it does: Timeout for all tasks via ollama_server
- When to fill: If ollama_server is slow
- Default value: Uses task timeout
- How to verify: This timeout should be used for ollama_server in logs

**DEEPSEEK_API_TIMEOUT_SECONDS**
- What it does: Timeout for all tasks via deepseek_api
- When to fill: If deepseek_api is slow
- Default value: Uses task timeout
- How to verify: This timeout should be used for deepseek_api in logs

### Per-Provider Per-Task Timeouts

**OLLAMA_LOCAL_TECH_TIMEOUT_SECONDS**
- What it does: Timeout for tech_analysis via ollama_local
- When to fill: If tech_analysis on ollama_local requires special timeout
- Default value: Uses OLLAMA_LOCAL_TIMEOUT_SECONDS or TECH_TIMEOUT_SECONDS
- How to verify: This timeout should be used in logs

**OLLAMA_LOCAL_NEWS_TIMEOUT_SECONDS**
- What it does: Timeout for news_analysis via ollama_local
- When to fill: If news_analysis on ollama_local requires special timeout
- Default value: `240.0`
- How to verify: This timeout should be used in logs

**OLLAMA_LOCAL_SYNTHESIS_TIMEOUT_SECONDS**
- What it does: Timeout for synthesis via ollama_local
- When to fill: If synthesis on ollama_local requires special timeout
- Default value: `240.0`
- How to verify: This timeout should be used in logs

**OLLAMA_LOCAL_VERIFIER_TIMEOUT_SECONDS**
- What it does: Timeout for verification via ollama_local
- When to fill: If verification on ollama_local requires special timeout
- Default value: `240.0`
- How to verify: This timeout should be used in logs

### LLM Providers

**OLLAMA_LOCAL_URL**
- What it does: Local Ollama server URL
- When to fill: If Ollama is on a different port or host
- Default value: `http://localhost:11434`
- How to verify: `curl http://localhost:11434/api/tags` should return model list

**OLLAMA_SERVER_URL**
- What it does: Remote Ollama server URL (RunPod or your server)
- When to fill: If using RUNTIME_ENV=server
- Default value: Not set
- How to verify: URL should be accessible, should not be localhost/127.0.0.1

**DEEPSEEK_API_KEY**
- What it does: DeepSeek API key
- When to fill: If using deepseek_api provider
- How to get: Register on deepseek.com, create API key in Dashboard
- Permissions: API access required
- How to verify: deepseek_api should be available in logs

**DEEPSEEK_API_BASE**
- What it does: DeepSeek API base URL
- When to fill: Only if using a different endpoint
- Default value: `https://api.deepseek.com`
- How to verify: No verification needed

**OPENAI_API_KEY**
- What it does: OpenAI API key (optional)
- When to fill: If planning to use OpenAI provider
- How to get: Register on platform.openai.com, create key in API keys
- Permissions: API access required, payment required
- How to verify: Provider should be available in health check

**OPENAI_API_BASE**
- What it does: OpenAI API base URL
- When to fill: Only if using a different endpoint
- Default value: `https://api.openai.com/v1`
- How to verify: No verification needed

**OPENAI_ORG_ID**
- What it does: OpenAI organization ID (optional)
- When to fill: If using organizational account
- How to get: In OpenAI organization settings
- How to verify: No verification needed

**GOOGLE_API_KEY**
- What it does: Google Gemini API key (optional)
- When to fill: If planning to use Gemini provider
- How to get: Register on makersuite.google.com, create API key
- Permissions: Gemini API access required
- How to verify: Provider should be available in health check

**GOOGLE_API_BASE**
- What it does: Google Gemini API base URL
- When to fill: Only if using a different endpoint
- Default value: `https://generativelanguage.googleapis.com/v1`
- How to verify: No verification needed

**PERPLEXITY_API_KEY**
- What it does: Perplexity API key (optional)
- When to fill: If planning to use Perplexity provider
- How to get: Register on perplexity.ai, create API key in Dashboard
- Permissions: API access required
- How to verify: Provider should be available in health check

**PERPLEXITY_API_BASE**
- What it does: Perplexity API base URL
- When to fill: Only if using a different endpoint
- Default value: `https://api.perplexity.ai`
- How to verify: No verification needed

### Task Routing

**LLM_LAST_RESORT_PROVIDER**
- What it does: Provider for last resort fallback
- When to fill: If a different last resort is needed
- Default value: `ollama_local`
- How to verify: This should be used when all providers are unavailable

**LLM_LAST_RESORT_MODEL**
- What it does: Model for last resort fallback
- When to fill: If a different model for last resort is needed
- Default value: `llama3:latest`
- How to verify: Last resort should use this model in logs

Variables for each task follow the pattern `{TASK}_{BRANCH}_{TYPE}_PROVIDER` and `{TASK}_{BRANCH}_{TYPE}_MODEL`, where:
- TASK: TECH, NEWS, SYNTHESIS, VERIFIER
- BRANCH: LOCAL, SERVER
- TYPE: PRIMARY, FALLBACK1, FALLBACK2, FALLBACK3

Examples: `TECH_LOCAL_PRIMARY_PROVIDER`, `NEWS_SERVER_FALLBACK1_MODEL`.

### Local Hardware Gating

**LOCAL_GPU_MIN_VRAM_GB**
- What it does: Minimum VRAM for using large models locally
- When to fill: If threshold needs to be changed
- Default value: `8.0`
- How to verify: `check_gpu.py` script uses this value for profile selection

**LOCAL_ALLOW_CPU_FALLBACK**
- What it does: Allow CPU usage if GPU is unavailable
- When to fill: If CPU fallback is needed
- Default value: `true`
- How to verify: CPU should be used when GPU is absent

### Hugging Face Cache

**MODEL_STORAGE_DIR**
- What it does: Root directory for all model caches
- When to fill: If a different directory is needed
- Default value: `models`
- How to verify: Caches should be created in specified directory

**HF_HOME**
- What it does: Hugging Face home directory (settings, tokens)
- When to fill: If a different directory is needed
- Default value: `models/.cache/huggingface`
- How to verify: HF settings should be saved here

**HUGGINGFACE_HUB_CACHE**
- What it does: Cache for downloaded Hugging Face models
- When to fill: If a different directory is needed
- Default value: `models/.cache/huggingface/hub`
- How to verify: Downloaded models should be here

**TRANSFORMERS_CACHE**
- What it does: Cache for transformers library
- When to fill: If a different directory is needed
- Default value: `models/.cache/huggingface/transformers`
- How to verify: Transformers cache should be here

**HF_DATASETS_CACHE**
- What it does: Cache for datasets
- When to fill: If using datasets
- Default value: `models/.cache/huggingface/datasets`
- How to verify: Datasets cache should be here

**HF_TOKENIZERS_CACHE**
- What it does: Cache for tokenizers
- When to fill: If a different directory is needed
- Default value: `models/.cache/huggingface/tokenizers`
- How to verify: Tokenizers cache should be here

**HF_MODULES_CACHE**
- What it does: Cache for custom modules from HF repositories
- When to fill: If a different directory is needed
- Default value: `models/.cache/huggingface/modules`
- How to verify: Modules cache should be here

**GGUF_CACHE_DIR**
- What it does: Directory for GGUF files
- When to fill: If downloading GGUF directly
- Default value: `models/gguf`
- How to verify: GGUF files should be here

**MODEL_BUILD_CACHE_DIR**
- What it does: Cache for compiled artifacts
- When to fill: If a different directory is needed
- Default value: `models/.cache/build`
- How to verify: Compiled artifacts should be here

**HF_HUB_DISABLE_PROGRESS_BARS**
- What it does: Disable progress bars for Hugging Face Hub
- When to fill: In non-interactive environments
- Default value: `1` (disabled)
- How to verify: No progress bars should appear during download

**TQDM_DISABLE**
- What it does: Disable progress bars for tqdm
- When to fill: In non-interactive environments
- Default value: `1` (disabled)
- How to verify: No progress bars should appear during download

**HF_TOKEN** / **HUGGINGFACE_HUB_TOKEN**
- What it does: Hugging Face token for accessing private models
- When to fill: If gated models are needed or higher rate limits
- How to get: Register on huggingface.co, create token in Settings -> Access Tokens
- Permissions: Read access is sufficient for downloading models
- How to verify: Gated models should download

### Logging

**LOG_LEVEL**
- What it does: Logging level (DEBUG, INFO, WARNING, ERROR)
- When to fill: If different detail level is needed
- Default value: `INFO`
- How to verify: Specified level should be in logs

**LOG_CONSOLE_LEVEL**
- What it does: Console logging level
- When to fill: If different console level is needed
- Default value: `WARNING`
- How to verify: Only messages of specified level should appear in console

**LOG_SPLIT_FILES**
- What it does: Split logs into files (app.log, errors.log, warnings.log)
- When to fill: If separate files are needed
- Default value: `true`
- How to verify: Separate log files should be created

**LOG_ENABLE_HTTP_FILE**
- What it does: Enable separate file for HTTP logs
- When to fill: If separate HTTP logs are needed
- Default value: `false`
- How to verify: http.log should be created

**LOG_MASK_AUTH**
- What it does: Mask secrets in logs
- When to fill: Should always be enabled
- Default value: `true`
- How to verify: API keys should not be visible in logs

**LOG_RETENTION**
- What it does: Log retention time
- When to fill: If different period is needed
- Default value: `90 days`
- How to verify: Old logs should be deleted

**LOG_COMPRESSION**
- What it does: Compression for old logs (zip or gz)
- When to fill: If different format is needed
- Default value: `zip`
- How to verify: Old logs should be compressed

## Timeouts

Timeout priority (from highest to lowest):

1. Per-provider per-task: `OLLAMA_LOCAL_{TASK}_TIMEOUT_SECONDS`
2. Per-provider: `OLLAMA_LOCAL_TIMEOUT_SECONDS`
3. Per-task: `{TASK}_TIMEOUT_SECONDS`
4. Global: `LLM_TIMEOUT_SECONDS`

Timeout recommendations:

- Ollama local (7B models): 180-300 seconds for news/synthesis/verification
- Ollama local (large models): 300-600 seconds
- Ollama server: 180-300 seconds (depends on server)
- DeepSeek API: 60-120 seconds (usually fast)
- Cloud API (OpenAI, Google): 60-120 seconds

## Hugging Face Progress and Cache

Variables affecting progress bars:
- `HF_HUB_DISABLE_PROGRESS_BARS=1` - disables HF Hub progress bars
- `TQDM_DISABLE=1` - disables tqdm progress bars

To enable progress bars, set these variables to empty values or remove them.

Cache is stored in the directory specified in `HUGGINGFACE_HUB_CACHE` (default `models/.cache/huggingface/hub`). To clear cache, delete this directory.

## Checklist: Minimal Working .env for Local

- [ ] `OANDA_API_KEY` - required
- [ ] `OANDA_ACCOUNT_ID` - required
- [ ] `OLLAMA_LOCAL_URL` - if using ollama_local (default http://localhost:11434)
- [ ] `RUNTIME_ENV=local` - required
- [ ] Configure at least one provider for each task (TECH_LOCAL_PRIMARY_PROVIDER/MODEL etc.)
- [ ] `LLM_LAST_RESORT_PROVIDER=ollama_local` - recommended
- [ ] `LLM_LAST_RESORT_MODEL=llama3:latest` - recommended

## Checklist: Minimal Working .env for Server

- [ ] `OANDA_API_KEY` - required
- [ ] `OANDA_ACCOUNT_ID` - required
- [ ] `OLLAMA_SERVER_URL` - required, must be valid URL (not localhost)
- [ ] `RUNTIME_ENV=server` - required
- [ ] Configure at least one provider for each task (TECH_SERVER_PRIMARY_PROVIDER/MODEL etc.)
- [ ] `LLM_LAST_RESORT_PROVIDER=ollama_local` - recommended
- [ ] `LLM_LAST_RESORT_MODEL=llama3:latest` - recommended
- [ ] `OLLAMA_LOCAL_URL` - for last resort fallback
