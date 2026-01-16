# Логирование

Проект использует [loguru](https://github.com/Delgan/loguru) для логирования. Система логирования настроена для обеспечения читаемого вывода в консоль и структурированного логирования в файлы с автоматической ротацией и маскированием секретов.

## Конфигурация

Настройки логирования управляются через переменные окружения в файле `.env`:

```env
# Директория для лог-файлов
LOG_DIR=logs

# Уровень логирования для файлов
LOG_LEVEL=INFO

# Уровень логирования для консоли
LOG_CONSOLE_LEVEL=INFO

# Формат логов (json|text)
LOG_FORMAT=json

# Ротация логов (время или размер)
LOG_ROTATION=00:00

# Хранение старых логов
LOG_RETENTION=30 days

# Сжатие старых логов
LOG_COMPRESSION=zip

# Маскирование секретов в логах
LOG_MASK_AUTH=true

# Уровень логирования для HTTP библиотек
LOG_HTTP_LEVEL=WARNING

# Разделение логов на отдельные файлы
LOG_SPLIT_FILES=true

# Включить отдельный файл для HTTP логов
LOG_ENABLE_HTTP_FILE=false
```

## Структура логов

### Консоль

По умолчанию в консоль выводятся только логи приложения уровня INFO и выше. Логи библиотек (httpx, httpcore) фильтруются, чтобы не засорять вывод.

Формат консольного вывода:
```
2024-01-15 10:30:45 | INFO | src.runtime.orchestrator:run_analysis:123 | Starting analysis for EURUSD
```

При использовании флага `--verbose` уровень консоли повышается до DEBUG, но только для логов приложения. HTTP библиотеки остаются на уровне WARNING.

### Файлы

Логи записываются в директорию, указанную в `LOG_DIR` (по умолчанию `logs/`).

#### Раздельные файлы (LOG_SPLIT_FILES=true)

- **app.log** — все логи уровня INFO и выше
- **warnings.log** — только WARNING и выше
- **errors.log** — только ERROR и выше
- **http.log** — логи HTTP библиотек (только если `LOG_ENABLE_HTTP_FILE=true`)

#### Единый файл (LOG_SPLIT_FILES=false)

- **app.log** — все логи уровня, указанного в `LOG_LEVEL`

Все файловые логи сохраняются в формате JSON для удобного парсинга и анализа.

## Маскирование секретов

При включенном `LOG_MASK_AUTH=true` система автоматически маскирует:

- **Authorization заголовки**: `Authorization: Bearer sk-...` → `Authorization: *****`
- **API ключи в URL**: `apiKey=secret123` → `apiKey=*****`
- **Значения переменных окружения**: `OPENAI_API_KEY=sk-...` → `OPENAI_API_KEY=*****`

Поддерживаемые переменные окружения:
- `OPENAI_API_KEY`
- `DEEPSEEK_API_KEY`
- `GOOGLE_API_KEY`
- `HF_TOKEN`
- `HUGGINGFACE_HUB_TOKEN`
- `NEWSAPI_API_KEY`
- `OANDA_API_KEY`
- `TWELVE_DATA_API_KEY`

## Ротация и хранение

- **LOG_ROTATION**: Время или размер для ротации (например, `00:00` — каждый день в полночь, `100 MB` — при достижении размера)
- **LOG_RETENTION**: Период хранения старых логов (например, `30 days`, `1 week`)
- **LOG_COMPRESSION**: Формат сжатия старых логов (`zip`, `gz`, `tar.gz`)

## Использование в коде

### Стандартный logging

Существующий код, использующий стандартный `logging`, продолжит работать без изменений:

```python
import logging
from src.utils.logging import get_logger

logger = get_logger(__name__)
logger.info("Message")
```

Все записи автоматически перенаправляются в loguru через `InterceptHandler`.

### Прямое использование loguru

В новых модулях можно использовать loguru напрямую:

```python
from loguru import logger

logger.info("Message")
logger.debug("Debug message")
logger.warning("Warning message")
logger.error("Error message")
```

## Фильтрация шума

Система автоматически снижает уровень логирования для шумных библиотек:

- `httpx` — WARNING
- `httpcore` — WARNING
- `urllib3` — WARNING
- `asyncio` — WARNING

Эти настройки применяются даже при `--verbose`, чтобы консоль оставалась читаемой.

## Примеры использования

### Базовое использование

```bash
python src/app/main.py analyze --symbol EURUSD --timeframe 1h
```

В консоль выводятся только важные логи приложения.

### Подробный режим

```bash
python src/app/main.py analyze --symbol EURUSD --timeframe 1h --verbose
```

В консоль выводятся DEBUG логи приложения, но HTTP библиотеки остаются на WARNING.

### Просмотр логов

```bash
# Все логи
cat logs/app.log | jq

# Только ошибки
cat logs/errors.log | jq

# HTTP логи (если включены)
cat logs/http.log | jq
```

## Настройка для разработки

Для разработки рекомендуется:

```env
LOG_LEVEL=DEBUG
LOG_CONSOLE_LEVEL=DEBUG
LOG_SPLIT_FILES=true
LOG_ENABLE_HTTP_FILE=false
```

## Настройка для продакшена

Для продакшена рекомендуется:

```env
LOG_LEVEL=INFO
LOG_CONSOLE_LEVEL=WARNING
LOG_SPLIT_FILES=true
LOG_ENABLE_HTTP_FILE=false
LOG_MASK_AUTH=true
LOG_RETENTION=90 days
LOG_COMPRESSION=zip
```
