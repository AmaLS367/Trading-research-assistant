# LLM Task Routing

## Обзор

LLM routing в проекте управляет выбором провайдеров и моделей для четырех задач: TECH (технический анализ), NEWS (анализ новостей), SYNTHESIS (синтез рекомендации), VERIFIER (верификация). Роутер выбирает ветку (local или server) на основе переменной RUNTIME_ENV, затем последовательно пробует провайдеры из выбранной ветки в порядке Primary -> Fallback1 -> Fallback2 -> Fallback3. Если все провайдеры ветки недоступны или завершились ошибкой, используется глобальный last resort (ollama_local/llama3:latest).

## Таблица маршрутизации

| Задача | Ветка | Primary | Fallback1 | Fallback2 | Last Resort |
|--------|-------|---------|-----------|-----------|-------------|
| TECH | local | deepseek_api/deepseek-chat | ollama_local/llama3:latest | - | ollama_local/llama3:latest |
| TECH | server | ollama_server/deepseek-r1:32b | ollama_server/qwen2.5:32b | deepseek_api/deepseek-chat | ollama_local/llama3:latest |
| NEWS | local | ollama_local/qwen2.5:7b | ollama_local/llama3:latest | - | ollama_local/llama3:latest |
| NEWS | server | ollama_server/qwen2.5:32b | ollama_server/fino1-8b | ollama_local/llama3:latest | ollama_local/llama3:latest |
| SYNTHESIS | local | ollama_local/llama3:latest | deepseek_api/deepseek-chat | - | ollama_local/llama3:latest |
| SYNTHESIS | server | ollama_server/llama3.1:70b | deepseek_api/deepseek-chat | ollama_local/llama3:latest | ollama_local/llama3:latest |
| VERIFIER | local | ollama_local/phi3.5:latest | deepseek_api/deepseek-chat | ollama_local/llama3:latest | ollama_local/llama3:latest |
| VERIFIER | server | ollama_server/granite3-8b:latest | deepseek_api/deepseek-chat | ollama_local/llama3:latest | ollama_local/llama3:latest |

## Как выбирается ветка

Ветка (local или server) выбирается на основе переменной окружения `RUNTIME_ENV`. Если `RUNTIME_ENV=local`, используются настройки с префиксом `*_LOCAL_*`. Если `RUNTIME_ENV=server`, используются настройки с префиксом `*_SERVER_*`.

В логах ветка не указывается явно, но можно определить по используемому провайдеру: если используется `ollama_server`, значит выбрана ветка server. Если используется `ollama_local` или `deepseek_api` при `RUNTIME_ENV=local`, значит выбрана ветка local.

## Как понять, какая модель реально использовалась

### В логах

Ищите строки с префиксом `Provider response success` или `Provider timeout`:

```
Provider response success: provider=ollama_local, model=qwen2.5:7b, duration_ms=1234.5, response_chars=500, attempts=1
```

При переключении на fallback появляется строка:

```
Switching to fallback: reason=timeout, next_provider=ollama_local, next_model=llama3:latest
```

При использовании last resort:

```
All configured providers failed for task=news_analysis, attempts=2, last_error=timeout, trying last resort (ollama_local/llama3:latest)
Last resort succeeded: provider=ollama_local, model=llama3:latest, attempts=3
```

### В артефактах

Для каждого run_id создается директория `artifacts/run_{run_id}/llm/` с поддиректориями для каждой задачи:
- `artifacts/run_{run_id}/llm/tech_analysis/response.json` - содержит поля `provider_name` и `model_name`
- `artifacts/run_{run_id}/llm/news_analysis/response.json`
- `artifacts/run_{run_id}/llm/synthesis/response.json`
- `artifacts/run_{run_id}/llm/verification/response.json` (если включен)

### В базе данных

В таблице `rationales` сохраняются поля `provider_name` и `model_name` для каждого типа rationale (TECHNICAL, NEWS, SYNTHESIS).

## Рекомендации для слабой VRAM

### Задачи для cloud (server)

- TECH: требует интерпретации индикаторов, лучше использовать большие модели на сервере
- SYNTHESIS: финальный синтез требует контекста, лучше большие модели

### Задачи для local

- NEWS: можно использовать модели 7B-8B (qwen2.5:7b, llama3:latest)
- VERIFIER: можно использовать небольшие модели (phi3.5:latest, granite3-8b)

### Если ollama local регулярно уходит в timeout

1. Увеличьте таймауты для конкретных задач через переменные:
   - `OLLAMA_LOCAL_NEWS_TIMEOUT_SECONDS=300`
   - `OLLAMA_LOCAL_SYNTHESIS_TIMEOUT_SECONDS=300`
   - `OLLAMA_LOCAL_VERIFIER_TIMEOUT_SECONDS=300`

2. Замените модель на меньшую:
   - Вместо `qwen2.5:7b` используйте `llama3:latest` (обычно быстрее)
   - Вместо `llama3:latest` используйте `phi3.5:latest` для verifier

3. Переключите задачу на cloud провайдер:
   - Установите `RUNTIME_ENV=server` для использования server ветки
   - Или измените primary провайдер на `deepseek_api` для конкретной задачи

---

**Подробные решения проблем LLM routing см. в [Руководстве по устранению неполадок](./troubleshooting.md#-проблемы-конфигурации-и-переменных-окружения).**
