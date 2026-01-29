# 🤖 LLM Task Routing

## Overview

LLM routing in the project manages provider and model selection for four tasks: TECH (technical analysis), NEWS (news analysis), SYNTHESIS (recommendation synthesis), VERIFIER (verification). The router selects a branch (local or server) based on the RUNTIME_ENV variable, then sequentially tries providers from the selected branch in order Primary -> Fallback1 -> Fallback2 -> Fallback3. If all branch providers are unavailable or fail, a global last resort (ollama_local/llama3:latest) is used.

## Routing Table

| Task | Branch | Primary | Fallback1 | Fallback2 | Last Resort |
|------|--------|---------|-----------|-----------|-------------|
| TECH | local | deepseek_api/deepseek-chat | ollama_local/llama3:latest | - | ollama_local/llama3:latest |
| TECH | server | ollama_server/deepseek-r1:32b | ollama_server/qwen2.5:32b | deepseek_api/deepseek-chat | ollama_local/llama3:latest |
| NEWS | local | ollama_local/qwen2.5:7b | ollama_local/llama3:latest | - | ollama_local/llama3:latest |
| NEWS | server | ollama_server/qwen2.5:32b | ollama_server/fino1-8b | ollama_local/llama3:latest | ollama_local/llama3:latest |
| SYNTHESIS | local | ollama_local/llama3:latest | deepseek_api/deepseek-chat | - | ollama_local/llama3:latest |
| SYNTHESIS | server | ollama_server/llama3.1:70b | deepseek_api/deepseek-chat | ollama_local/llama3:latest | ollama_local/llama3:latest |
| VERIFIER | local | ollama_local/phi3.5:latest | deepseek_api/deepseek-chat | ollama_local/llama3:latest | ollama_local/llama3:latest |
| VERIFIER | server | ollama_server/granite3.3:8b | deepseek_api/deepseek-chat | ollama_local/llama3:latest | ollama_local/llama3:latest |

## How Branch is Selected

The branch (local or server) is selected based on the `RUNTIME_ENV` environment variable. If `RUNTIME_ENV=local`, settings with the `*_LOCAL_*` prefix are used. If `RUNTIME_ENV=server`, settings with the `*_SERVER_*` prefix are used.

In logs, the branch is not explicitly indicated, but can be determined by the provider used: if `ollama_server` is used, the server branch was selected. If `ollama_local` or `deepseek_api` is used with `RUNTIME_ENV=local`, the local branch was selected.

## How to Determine Which Model Was Actually Used

### In Logs

Look for lines with the `Provider response success` or `Provider timeout` prefix:

```
Provider response success: provider=ollama_local, model=qwen2.5:7b, duration_ms=1234.5, response_chars=500, attempts=1
```

When switching to fallback, a line appears:

```
Switching to fallback: reason=timeout, next_provider=ollama_local, next_model=llama3:latest
```

When using last resort:

```
All configured providers failed for task=news_analysis, attempts=2, last_error=timeout, trying last resort (ollama_local/llama3:latest)
Last resort succeeded: provider=ollama_local, model=llama3:latest, attempts=3
```

### In Artifacts

For each run_id, a directory `artifacts/run_{run_id}/llm/` is created with subdirectories for each task:
- `artifacts/run_{run_id}/llm/tech_analysis/response.json` - contains `provider_name` and `model_name` fields
- `artifacts/run_{run_id}/llm/news_analysis/response.json`
- `artifacts/run_{run_id}/llm/synthesis/response.json`
- `artifacts/run_{run_id}/llm/verification/response.json` (if enabled)

### In Database

In the `rationales` table, `provider_name` and `model_name` fields are saved for each rationale type (TECHNICAL, NEWS, SYNTHESIS).

## Recommendations for Low VRAM

### Tasks for Cloud (Server)

- TECH: Requires indicator interpretation, better to use large models on server
- SYNTHESIS: Final synthesis requires context, better large models

### Tasks for Local

- NEWS: Can use 7B-8B models (qwen2.5:7b, llama3:latest)
- VERIFIER: Can use small models (phi3.5:latest, granite3.3:8b)

### If ollama local Regularly Times Out

1. Increase timeouts for specific tasks via variables:
   - `OLLAMA_LOCAL_NEWS_TIMEOUT_SECONDS=300`
   - `OLLAMA_LOCAL_SYNTHESIS_TIMEOUT_SECONDS=300`
   - `OLLAMA_LOCAL_VERIFIER_TIMEOUT_SECONDS=300`

2. Replace model with a smaller one:
   - Instead of `qwen2.5:7b` use `llama3:latest` (usually faster)
   - Instead of `llama3:latest` use `phi3.5:latest` for verifier

3. Switch task to cloud provider:
   - Set `RUNTIME_ENV=server` to use server branch
   - Or change primary provider to `deepseek_api` for specific task

---

**For detailed LLM routing troubleshooting, see [Troubleshooting Guide](./troubleshooting.md#-configuration-and-environment-variable-issues).**
