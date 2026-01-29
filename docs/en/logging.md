# 📝 Logging

The project uses [loguru](https://github.com/Delgan/loguru) for logging. The logging system is configured to provide readable console output and structured file logging with automatic rotation and secret masking.

## Configuration

Logging settings are managed through environment variables in the `.env` file:

```env
# Directory for log files
LOG_DIR=logs

# Log level for files
LOG_LEVEL=INFO

# Log level for console
LOG_CONSOLE_LEVEL=INFO

# Log format (json|text)
LOG_FORMAT=json

# Log rotation (time or size)
LOG_ROTATION=00:00

# Retention period for old logs
LOG_RETENTION=30 days

# Compression for old logs
LOG_COMPRESSION=zip

# Mask secrets in logs
LOG_MASK_AUTH=true

# Log level for HTTP libraries
LOG_HTTP_LEVEL=WARNING

# Split logs into separate files
LOG_SPLIT_FILES=true

# Enable separate file for HTTP logs
LOG_ENABLE_HTTP_FILE=false
```

## Log Structure

### Console

By default, only application logs at INFO level and above are displayed in the console. Library logs (httpx, httpcore) are filtered to avoid cluttering the output.

Console output format:
```
2024-01-15 10:30:45 | INFO | src.runtime.orchestrator:run_analysis:123 | Starting analysis for EURUSD
```

When using the `--verbose` flag, the console level is raised to DEBUG, but only for application logs. HTTP libraries remain at WARNING level.

### Files

Logs are written to the directory specified in `LOG_DIR` (default `logs/`).

#### Split Files (LOG_SPLIT_FILES=true)

- **app.log** — all logs at INFO level and above
- **warnings.log** — only WARNING and above
- **errors.log** — only ERROR and above
- **http.log** — HTTP library logs (only if `LOG_ENABLE_HTTP_FILE=true`)

#### Single File (LOG_SPLIT_FILES=false)

- **app.log** — all logs at the level specified in `LOG_LEVEL`

All file logs are saved in JSON format for easy parsing and analysis.

## Secret Masking

When `LOG_MASK_AUTH=true` is enabled, the system automatically masks:

- **Authorization headers**: `Authorization: Bearer sk-...` → `Authorization: *****`
- **API keys in URLs**: `apiKey=secret123` → `apiKey=*****`
- **Environment variable values**: `OPENAI_API_KEY=sk-...` → `OPENAI_API_KEY=*****`

Supported environment variables:
- `OPENAI_API_KEY`
- `DEEPSEEK_API_KEY`
- `GOOGLE_API_KEY`
- `HF_TOKEN`
- `HUGGINGFACE_HUB_TOKEN`
- `NEWSAPI_API_KEY`
- `OANDA_API_KEY`
- `TWELVE_DATA_API_KEY`

## Rotation and Retention

- **LOG_ROTATION**: Time or size for rotation (e.g., `00:00` — daily at midnight, `100 MB` — when size is reached)
- **LOG_RETENTION**: Retention period for old logs (e.g., `30 days`, `1 week`)
- **LOG_COMPRESSION**: Compression format for old logs (`zip`, `gz`, `tar.gz`)

## Usage in Code

### Standard logging

Existing code using standard `logging` will continue to work without changes:

```python
import logging
from src.utils.logging import get_logger

logger = get_logger(__name__)
logger.info("Message")
```

All records are automatically forwarded to loguru via `InterceptHandler`.

### Direct loguru usage

In new modules, you can use loguru directly:

```python
from loguru import logger

logger.info("Message")
logger.debug("Debug message")
logger.warning("Warning message")
logger.error("Error message")
```

## Noise Filtering

The system automatically reduces log levels for noisy libraries:

- `httpx` — WARNING
- `httpcore` — WARNING
- `urllib3` — WARNING
- `asyncio` — WARNING

These settings apply even with `--verbose` to keep the console readable.

## Usage Examples

### Basic Usage

```bash
python src/app/main.py analyze --symbol EURUSD --timeframe 1h
```

Only important application logs are displayed in the console.

### Verbose Mode

```bash
python src/app/main.py analyze --symbol EURUSD --timeframe 1h --verbose
```

DEBUG logs from the application are displayed in the console, but HTTP libraries remain at WARNING.

### Viewing Logs

```bash
# All logs
cat logs/app.log | jq

# Errors only
cat logs/errors.log | jq

# HTTP logs (if enabled)
cat logs/http.log | jq
```

## Development Configuration

For development, recommended settings:

```env
LOG_LEVEL=DEBUG
LOG_CONSOLE_LEVEL=DEBUG
LOG_SPLIT_FILES=true
LOG_ENABLE_HTTP_FILE=false
```

## Production Configuration

For production, recommended settings:

```env
LOG_LEVEL=INFO
LOG_CONSOLE_LEVEL=WARNING
LOG_SPLIT_FILES=true
LOG_ENABLE_HTTP_FILE=false
LOG_MASK_AUTH=true
LOG_RETENTION=90 days
LOG_COMPRESSION=zip
```
