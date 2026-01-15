from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Annotated

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


@dataclass
class LlmRouteStep:
    provider: str
    model: str


@dataclass
class LlmTaskRouting:
    steps: list[LlmRouteStep]


@dataclass
class LlmRoutingConfig:
    router_mode: str
    verifier_enabled: bool
    max_retries: int
    timeout_seconds: float
    temperature: float


class Settings(BaseSettings):
    # --- Application ---
    app_env: Annotated[str, Field(alias="APP_ENV")] = "development"
    app_timezone: Annotated[str, Field(alias="APP_TIMEZONE")] = "Asia/Yerevan"

    # --- OANDA API ---
    oanda_api_key: Annotated[str, Field(alias="OANDA_API_KEY")] = ""
    oanda_account_id: Annotated[str, Field(alias="OANDA_ACCOUNT_ID")] = ""
    oanda_base_url: Annotated[str, Field(alias="OANDA_BASE_URL")] = (
        "https://api-fxpractice.oanda.com"
    )

    # --- Twelve Data API ---
    twelve_data_api_key: Annotated[str, Field(alias="TWELVE_DATA_API_KEY")] = ""
    twelve_data_base_url: Annotated[str, Field(alias="TWELVE_DATA_BASE_URL")] = (
        "https://api.twelvedata.com"
    )

    # --- GDELT API ---
    gdelt_base_url: Annotated[str, Field(alias="GDELT_BASE_URL")] = "https://api.gdeltproject.org"

    # --- NewsAPI ---
    newsapi_api_key: Annotated[str, Field(alias="NEWSAPI_API_KEY")] = ""
    newsapi_base_url: Annotated[str, Field(alias="NEWSAPI_BASE_URL")] = "https://newsapi.org"

    # --- Ollama (legacy, for backward compatibility) ---
    ollama_base_url: Annotated[str, Field(alias="OLLAMA_BASE_URL")] = "http://localhost:11434"
    ollama_remote_base_url: Annotated[str | None, Field(alias="OLLAMA_REMOTE_BASE_URL")] = None
    ollama_model: Annotated[str, Field(alias="OLLAMA_MODEL")] = ""

    # --- LLM Providers (new multi-provider config) ---
    ollama_local_url: Annotated[str | None, Field(alias="OLLAMA_LOCAL_URL")] = None
    ollama_server_url: Annotated[str | None, Field(alias="OLLAMA_SERVER_URL")] = None
    deepseek_api_key: Annotated[str | None, Field(alias="DEEPSEEK_API_KEY")] = None
    deepseek_api_base: Annotated[str | None, Field(alias="DEEPSEEK_API_BASE")] = None

    # --- LLM Router Config ---
    llm_router_mode: Annotated[str, Field(alias="LLM_ROUTER_MODE")] = "sequential"
    llm_verifier_enabled: Annotated[bool, Field(alias="LLM_VERIFIER_ENABLED")] = False
    llm_verifier_mode: Annotated[str, Field(alias="LLM_VERIFIER_MODE")] = "soft"
    llm_verifier_max_repairs: Annotated[int, Field(alias="LLM_VERIFIER_MAX_REPAIRS")] = 1
    llm_max_retries: Annotated[int, Field(alias="LLM_MAX_RETRIES")] = 3
    llm_timeout_seconds: Annotated[float, Field(alias="LLM_TIMEOUT_SECONDS")] = 60.0
    llm_temperature: Annotated[float, Field(alias="LLM_TEMPERATURE")] = 0.2

    # --- Task Routing (TECH) ---
    tech_primary_provider: Annotated[str | None, Field(alias="TECH_PRIMARY_PROVIDER")] = None
    tech_primary_model: Annotated[str | None, Field(alias="TECH_PRIMARY_MODEL")] = None
    tech_fallback1_provider: Annotated[str | None, Field(alias="TECH_FALLBACK1_PROVIDER")] = None
    tech_fallback1_model: Annotated[str | None, Field(alias="TECH_FALLBACK1_MODEL")] = None
    tech_fallback2_provider: Annotated[str | None, Field(alias="TECH_FALLBACK2_PROVIDER")] = None
    tech_fallback2_model: Annotated[str | None, Field(alias="TECH_FALLBACK2_MODEL")] = None

    # --- Task Routing (NEWS) ---
    news_primary_provider: Annotated[str | None, Field(alias="NEWS_PRIMARY_PROVIDER")] = None
    news_primary_model: Annotated[str | None, Field(alias="NEWS_PRIMARY_MODEL")] = None
    news_fallback1_provider: Annotated[str | None, Field(alias="NEWS_FALLBACK1_PROVIDER")] = None
    news_fallback1_model: Annotated[str | None, Field(alias="NEWS_FALLBACK1_MODEL")] = None
    news_fallback2_provider: Annotated[str | None, Field(alias="NEWS_FALLBACK2_PROVIDER")] = None
    news_fallback2_model: Annotated[str | None, Field(alias="NEWS_FALLBACK2_MODEL")] = None

    # --- Task Routing (SYNTHESIS) ---
    synthesis_primary_provider: Annotated[str | None, Field(alias="SYNTHESIS_PRIMARY_PROVIDER")] = (
        None
    )
    synthesis_primary_model: Annotated[str | None, Field(alias="SYNTHESIS_PRIMARY_MODEL")] = None
    synthesis_fallback1_provider: Annotated[
        str | None, Field(alias="SYNTHESIS_FALLBACK1_PROVIDER")
    ] = None
    synthesis_fallback1_model: Annotated[str | None, Field(alias="SYNTHESIS_FALLBACK1_MODEL")] = (
        None
    )
    synthesis_fallback2_provider: Annotated[
        str | None, Field(alias="SYNTHESIS_FALLBACK2_PROVIDER")
    ] = None
    synthesis_fallback2_model: Annotated[str | None, Field(alias="SYNTHESIS_FALLBACK2_MODEL")] = (
        None
    )

    # --- Task Routing (VERIFIER) ---
    verifier_primary_provider: Annotated[str | None, Field(alias="VERIFIER_PRIMARY_PROVIDER")] = (
        None
    )
    verifier_primary_model: Annotated[str | None, Field(alias="VERIFIER_PRIMARY_MODEL")] = None
    verifier_fallback1_provider: Annotated[
        str | None, Field(alias="VERIFIER_FALLBACK1_PROVIDER")
    ] = None
    verifier_fallback1_model: Annotated[str | None, Field(alias="VERIFIER_FALLBACK1_MODEL")] = None
    verifier_fallback2_provider: Annotated[
        str | None, Field(alias="VERIFIER_FALLBACK2_PROVIDER")
    ] = None
    verifier_fallback2_model: Annotated[str | None, Field(alias="VERIFIER_FALLBACK2_MODEL")] = None

    # --- Per-Task Overrides ---
    tech_timeout_seconds: Annotated[float | None, Field(alias="TECH_TIMEOUT_SECONDS")] = None
    tech_temperature: Annotated[float | None, Field(alias="TECH_TEMPERATURE")] = None
    news_timeout_seconds: Annotated[float | None, Field(alias="NEWS_TIMEOUT_SECONDS")] = None
    news_temperature: Annotated[float | None, Field(alias="NEWS_TEMPERATURE")] = None
    synthesis_timeout_seconds: Annotated[float | None, Field(alias="SYNTHESIS_TIMEOUT_SECONDS")] = (
        None
    )
    synthesis_temperature: Annotated[float | None, Field(alias="SYNTHESIS_TEMPERATURE")] = None
    verifier_timeout_seconds: Annotated[float | None, Field(alias="VERIFIER_TIMEOUT_SECONDS")] = (
        None
    )
    verifier_temperature: Annotated[float | None, Field(alias="VERIFIER_TEMPERATURE")] = None

    # --- Storage ---
    storage_sqlite_db_path: Annotated[Path, Field(alias="STORAGE_SQLITE_DB_PATH")] = Path(
        "db/forex_research_assistant.sqlite3"
    )
    storage_artifacts_dir: Annotated[Path, Field(alias="STORAGE_ARTIFACTS_DIR")] = Path("artifacts")
    storage_migration_path: Annotated[str, Field(alias="STORAGE_MIGRATION_PATH")] = (
        "src/storage/sqlite/migrations"
    )

    # --- Runtime ---
    runtime_mvp_symbols_raw: Annotated[str, Field(alias="RUNTIME_MVP_SYMBOLS_RAW")] = (
        "EURUSD,GBPUSD,USDJPY"
    )
    runtime_mvp_timeframe: Annotated[str, Field(alias="RUNTIME_MVP_TIMEFRAME")] = "1m"
    runtime_mvp_expiry_seconds: Annotated[int, Field(alias="RUNTIME_MVP_EXPIRY_SECONDS")] = 60
    runtime_llm_enabled: Annotated[bool, Field(alias="RUNTIME_LLM_ENABLED")] = False
    runtime_llm_call_interval_seconds: Annotated[
        int, Field(alias="RUNTIME_LLM_CALL_INTERVAL_SECONDS")
    ] = 300
    runtime_news_refresh_interval_seconds: Annotated[
        int, Field(alias="RUNTIME_NEWS_REFRESH_INTERVAL_SECONDS")
    ] = 300
    runtime_market_data_window_candles: Annotated[
        int, Field(alias="RUNTIME_MARKET_DATA_WINDOW_CANDLES")
    ] = 300

    @field_validator("runtime_mvp_timeframe", mode="before")
    @classmethod
    def validate_timeframe(cls, value: str) -> str:
        normalized_value = str(value).strip().lower()
        allowed_values = {"1m", "5m", "15m", "30m", "1h", "4h", "1d"}
        if normalized_value not in allowed_values:
            raise ValueError(f"Unsupported timeframe: {normalized_value}")
        return normalized_value

    @field_validator(
        "runtime_mvp_expiry_seconds",
        "runtime_llm_call_interval_seconds",
        "runtime_news_refresh_interval_seconds",
        mode="before",
    )
    @classmethod
    def validate_positive_seconds(cls, value: int) -> int:
        int_value = int(value)
        if int_value <= 0:
            raise ValueError("Seconds value must be positive")
        return int_value

    @field_validator("runtime_market_data_window_candles", mode="before")
    @classmethod
    def validate_market_data_window(cls, value: int) -> int:
        int_value = int(value)
        if int_value < 50:
            raise ValueError("market_data_window_candles must be at least 50")
        return int_value

    @field_validator("storage_sqlite_db_path", "storage_artifacts_dir", mode="before")
    @classmethod
    def _as_path(cls, value: str | Path) -> Path:
        if isinstance(value, Path):
            return value
        return Path(str(value))

    @field_validator(
        "ollama_local_url",
        "ollama_server_url",
        "deepseek_api_base",
        mode="before",
    )
    @classmethod
    def _normalize_url(cls, value: str | None) -> str | None:
        if value is None or value == "":
            return None
        normalized = str(value).strip()
        if not normalized:
            return None
        if not normalized.startswith(("http://", "https://")):
            return None
        return normalized

    @field_validator("deepseek_api_key", mode="before")
    @classmethod
    def _normalize_api_key(cls, value: str | None) -> str | None:
        if value is None or value == "":
            return None
        normalized = str(value).strip()
        if not normalized:
            return None
        return normalized

    def mvp_symbols(self) -> list[str]:
        raw_parts = self.runtime_mvp_symbols_raw.split(",")
        normalized_symbols: list[str] = []
        for part in raw_parts:
            cleaned_value = part.strip().upper()
            if not cleaned_value:
                continue
            normalized_symbols.append(cleaned_value)
        if not normalized_symbols:
            raise ValueError("MVP_SYMBOLS is empty after parsing")
        return normalized_symbols

    def is_development(self) -> bool:
        return self.app_env.strip().lower() == "development"

    def _get_ollama_local_url(self) -> str:
        if self.ollama_local_url:
            return self.ollama_local_url
        return self.ollama_base_url

    def _get_ollama_server_url(self) -> str | None:
        if self.ollama_server_url:
            return self.ollama_server_url
        return self.ollama_remote_base_url

    def _build_task_routing(self, task_prefix: str) -> LlmTaskRouting:
        steps: list[LlmRouteStep] = []

        primary_provider = getattr(self, f"{task_prefix}_primary_provider", None)
        primary_model = getattr(self, f"{task_prefix}_primary_model", None)
        if primary_provider and primary_model:
            steps.append(LlmRouteStep(provider=primary_provider, model=primary_model))

        fallback1_provider = getattr(self, f"{task_prefix}_fallback1_provider", None)
        fallback1_model = getattr(self, f"{task_prefix}_fallback1_model", None)
        if fallback1_provider and fallback1_model:
            steps.append(LlmRouteStep(provider=fallback1_provider, model=fallback1_model))

        fallback2_provider = getattr(self, f"{task_prefix}_fallback2_provider", None)
        fallback2_model = getattr(self, f"{task_prefix}_fallback2_model", None)
        if fallback2_provider and fallback2_model:
            steps.append(LlmRouteStep(provider=fallback2_provider, model=fallback2_model))

        if not steps:
            default_model = self.ollama_model or "llama3:latest"
            steps.append(LlmRouteStep(provider="ollama_local", model=default_model))

        return LlmTaskRouting(steps=steps)

    def get_tech_routing(self) -> LlmTaskRouting:
        return self._build_task_routing("tech")

    def get_news_routing(self) -> LlmTaskRouting:
        return self._build_task_routing("news")

    def get_synthesis_routing(self) -> LlmTaskRouting:
        return self._build_task_routing("synthesis")

    def get_verifier_routing(self) -> LlmTaskRouting:
        return self._build_task_routing("verifier")

    def get_llm_routing_config(self) -> LlmRoutingConfig:
        return LlmRoutingConfig(
            router_mode=self.llm_router_mode,
            verifier_enabled=self.llm_verifier_enabled,
            max_retries=self.llm_max_retries,
            timeout_seconds=self.llm_timeout_seconds,
            temperature=self.llm_temperature,
        )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        env_prefix="",
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
