from pydantic import BaseModel, ConfigDict


class LlmRequest(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    task: str
    system_prompt: str
    user_prompt: str
    temperature: float
    timeout_seconds: float
    max_retries: int
    model_name: str | None = None
    response_format: str | None = None


class LlmResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    text: str
    provider_name: str
    model_name: str
    latency_ms: int
    attempts: int
    error: str | None = None
