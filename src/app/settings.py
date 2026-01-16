from __future__ import annotations

import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Annotated, Literal
from urllib.parse import urlparse

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


@dataclass
class LlmRouteStep:
    provider: str
    model: str


@dataclass
class RouteCandidate:
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
    tech_fallback3_provider: Annotated[str | None, Field(alias="TECH_FALLBACK3_PROVIDER")] = None
    tech_fallback3_model: Annotated[str | None, Field(alias="TECH_FALLBACK3_MODEL")] = None

    # --- Task Routing (NEWS) ---
    news_primary_provider: Annotated[str | None, Field(alias="NEWS_PRIMARY_PROVIDER")] = None
    news_primary_model: Annotated[str | None, Field(alias="NEWS_PRIMARY_MODEL")] = None
    news_fallback1_provider: Annotated[str | None, Field(alias="NEWS_FALLBACK1_PROVIDER")] = None
    news_fallback1_model: Annotated[str | None, Field(alias="NEWS_FALLBACK1_MODEL")] = None
    news_fallback2_provider: Annotated[str | None, Field(alias="NEWS_FALLBACK2_PROVIDER")] = None
    news_fallback2_model: Annotated[str | None, Field(alias="NEWS_FALLBACK2_MODEL")] = None
    news_fallback3_provider: Annotated[str | None, Field(alias="NEWS_FALLBACK3_PROVIDER")] = None
    news_fallback3_model: Annotated[str | None, Field(alias="NEWS_FALLBACK3_MODEL")] = None

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
    synthesis_fallback3_provider: Annotated[
        str | None, Field(alias="SYNTHESIS_FALLBACK3_PROVIDER")
    ] = None
    synthesis_fallback3_model: Annotated[str | None, Field(alias="SYNTHESIS_FALLBACK3_MODEL")] = (
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
    verifier_fallback3_provider: Annotated[
        str | None, Field(alias="VERIFIER_FALLBACK3_PROVIDER")
    ] = None
    verifier_fallback3_model: Annotated[str | None, Field(alias="VERIFIER_FALLBACK3_MODEL")] = None

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
    runtime_env: Annotated[Literal["local", "server"], Field(alias="RUNTIME_ENV")] = "local"
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

    # --- LLM Last Resort ---
    llm_last_resort_provider: Annotated[str | None, Field(alias="LLM_LAST_RESORT_PROVIDER")] = None
    llm_last_resort_model: Annotated[str | None, Field(alias="LLM_LAST_RESORT_MODEL")] = None

    # --- Task Routing (NEW SCHEMA - TECH) ---
    tech_local_primary_provider: Annotated[
        str | None, Field(alias="TECH_LOCAL_PRIMARY_PROVIDER")
    ] = None
    tech_local_primary_model: Annotated[str | None, Field(alias="TECH_LOCAL_PRIMARY_MODEL")] = None
    tech_local_fallback1_provider: Annotated[
        str | None, Field(alias="TECH_LOCAL_FALLBACK1_PROVIDER")
    ] = None
    tech_local_fallback1_model: Annotated[str | None, Field(alias="TECH_LOCAL_FALLBACK1_MODEL")] = (
        None
    )
    tech_local_fallback2_provider: Annotated[
        str | None, Field(alias="TECH_LOCAL_FALLBACK2_PROVIDER")
    ] = None
    tech_local_fallback2_model: Annotated[str | None, Field(alias="TECH_LOCAL_FALLBACK2_MODEL")] = (
        None
    )
    tech_local_fallback3_provider: Annotated[
        str | None, Field(alias="TECH_LOCAL_FALLBACK3_PROVIDER")
    ] = None
    tech_local_fallback3_model: Annotated[str | None, Field(alias="TECH_LOCAL_FALLBACK3_MODEL")] = (
        None
    )

    tech_server_primary_provider: Annotated[
        str | None, Field(alias="TECH_SERVER_PRIMARY_PROVIDER")
    ] = None
    tech_server_primary_model: Annotated[str | None, Field(alias="TECH_SERVER_PRIMARY_MODEL")] = (
        None
    )
    tech_server_fallback1_provider: Annotated[
        str | None, Field(alias="TECH_SERVER_FALLBACK1_PROVIDER")
    ] = None
    tech_server_fallback1_model: Annotated[
        str | None, Field(alias="TECH_SERVER_FALLBACK1_MODEL")
    ] = None
    tech_server_fallback2_provider: Annotated[
        str | None, Field(alias="TECH_SERVER_FALLBACK2_PROVIDER")
    ] = None
    tech_server_fallback2_model: Annotated[
        str | None, Field(alias="TECH_SERVER_FALLBACK2_MODEL")
    ] = None
    tech_server_fallback3_provider: Annotated[
        str | None, Field(alias="TECH_SERVER_FALLBACK3_PROVIDER")
    ] = None
    tech_server_fallback3_model: Annotated[
        str | None, Field(alias="TECH_SERVER_FALLBACK3_MODEL")
    ] = None

    # --- Task Routing (NEW SCHEMA - NEWS) ---
    news_local_primary_provider: Annotated[
        str | None, Field(alias="NEWS_LOCAL_PRIMARY_PROVIDER")
    ] = None
    news_local_primary_model: Annotated[str | None, Field(alias="NEWS_LOCAL_PRIMARY_MODEL")] = None
    news_local_fallback1_provider: Annotated[
        str | None, Field(alias="NEWS_LOCAL_FALLBACK1_PROVIDER")
    ] = None
    news_local_fallback1_model: Annotated[str | None, Field(alias="NEWS_LOCAL_FALLBACK1_MODEL")] = (
        None
    )
    news_local_fallback2_provider: Annotated[
        str | None, Field(alias="NEWS_LOCAL_FALLBACK2_PROVIDER")
    ] = None
    news_local_fallback2_model: Annotated[str | None, Field(alias="NEWS_LOCAL_FALLBACK2_MODEL")] = (
        None
    )
    news_local_fallback3_provider: Annotated[
        str | None, Field(alias="NEWS_LOCAL_FALLBACK3_PROVIDER")
    ] = None
    news_local_fallback3_model: Annotated[str | None, Field(alias="NEWS_LOCAL_FALLBACK3_MODEL")] = (
        None
    )

    news_server_primary_provider: Annotated[
        str | None, Field(alias="NEWS_SERVER_PRIMARY_PROVIDER")
    ] = None
    news_server_primary_model: Annotated[str | None, Field(alias="NEWS_SERVER_PRIMARY_MODEL")] = (
        None
    )
    news_server_fallback1_provider: Annotated[
        str | None, Field(alias="NEWS_SERVER_FALLBACK1_PROVIDER")
    ] = None
    news_server_fallback1_model: Annotated[
        str | None, Field(alias="NEWS_SERVER_FALLBACK1_MODEL")
    ] = None
    news_server_fallback2_provider: Annotated[
        str | None, Field(alias="NEWS_SERVER_FALLBACK2_PROVIDER")
    ] = None
    news_server_fallback2_model: Annotated[
        str | None, Field(alias="NEWS_SERVER_FALLBACK2_MODEL")
    ] = None
    news_server_fallback3_provider: Annotated[
        str | None, Field(alias="NEWS_SERVER_FALLBACK3_PROVIDER")
    ] = None
    news_server_fallback3_model: Annotated[
        str | None, Field(alias="NEWS_SERVER_FALLBACK3_MODEL")
    ] = None

    # --- Task Routing (NEW SCHEMA - SYNTHESIS) ---
    synthesis_local_primary_provider: Annotated[
        str | None, Field(alias="SYNTHESIS_LOCAL_PRIMARY_PROVIDER")
    ] = None
    synthesis_local_primary_model: Annotated[
        str | None, Field(alias="SYNTHESIS_LOCAL_PRIMARY_MODEL")
    ] = None
    synthesis_local_fallback1_provider: Annotated[
        str | None, Field(alias="SYNTHESIS_LOCAL_FALLBACK1_PROVIDER")
    ] = None
    synthesis_local_fallback1_model: Annotated[
        str | None, Field(alias="SYNTHESIS_LOCAL_FALLBACK1_MODEL")
    ] = None
    synthesis_local_fallback2_provider: Annotated[
        str | None, Field(alias="SYNTHESIS_LOCAL_FALLBACK2_PROVIDER")
    ] = None
    synthesis_local_fallback2_model: Annotated[
        str | None, Field(alias="SYNTHESIS_LOCAL_FALLBACK2_MODEL")
    ] = None
    synthesis_local_fallback3_provider: Annotated[
        str | None, Field(alias="SYNTHESIS_LOCAL_FALLBACK3_PROVIDER")
    ] = None
    synthesis_local_fallback3_model: Annotated[
        str | None, Field(alias="SYNTHESIS_LOCAL_FALLBACK3_MODEL")
    ] = None

    synthesis_server_primary_provider: Annotated[
        str | None, Field(alias="SYNTHESIS_SERVER_PRIMARY_PROVIDER")
    ] = None
    synthesis_server_primary_model: Annotated[
        str | None, Field(alias="SYNTHESIS_SERVER_PRIMARY_MODEL")
    ] = None
    synthesis_server_fallback1_provider: Annotated[
        str | None, Field(alias="SYNTHESIS_SERVER_FALLBACK1_PROVIDER")
    ] = None
    synthesis_server_fallback1_model: Annotated[
        str | None, Field(alias="SYNTHESIS_SERVER_FALLBACK1_MODEL")
    ] = None
    synthesis_server_fallback2_provider: Annotated[
        str | None, Field(alias="SYNTHESIS_SERVER_FALLBACK2_PROVIDER")
    ] = None
    synthesis_server_fallback2_model: Annotated[
        str | None, Field(alias="SYNTHESIS_SERVER_FALLBACK2_MODEL")
    ] = None
    synthesis_server_fallback3_provider: Annotated[
        str | None, Field(alias="SYNTHESIS_SERVER_FALLBACK3_PROVIDER")
    ] = None
    synthesis_server_fallback3_model: Annotated[
        str | None, Field(alias="SYNTHESIS_SERVER_FALLBACK3_MODEL")
    ] = None

    # --- Task Routing (NEW SCHEMA - VERIFIER) ---
    verifier_local_primary_provider: Annotated[
        str | None, Field(alias="VERIFIER_LOCAL_PRIMARY_PROVIDER")
    ] = None
    verifier_local_primary_model: Annotated[
        str | None, Field(alias="VERIFIER_LOCAL_PRIMARY_MODEL")
    ] = None
    verifier_local_fallback1_provider: Annotated[
        str | None, Field(alias="VERIFIER_LOCAL_FALLBACK1_PROVIDER")
    ] = None
    verifier_local_fallback1_model: Annotated[
        str | None, Field(alias="VERIFIER_LOCAL_FALLBACK1_MODEL")
    ] = None
    verifier_local_fallback2_provider: Annotated[
        str | None, Field(alias="VERIFIER_LOCAL_FALLBACK2_PROVIDER")
    ] = None
    verifier_local_fallback2_model: Annotated[
        str | None, Field(alias="VERIFIER_LOCAL_FALLBACK2_MODEL")
    ] = None
    verifier_local_fallback3_provider: Annotated[
        str | None, Field(alias="VERIFIER_LOCAL_FALLBACK3_PROVIDER")
    ] = None
    verifier_local_fallback3_model: Annotated[
        str | None, Field(alias="VERIFIER_LOCAL_FALLBACK3_MODEL")
    ] = None

    verifier_server_primary_provider: Annotated[
        str | None, Field(alias="VERIFIER_SERVER_PRIMARY_PROVIDER")
    ] = None
    verifier_server_primary_model: Annotated[
        str | None, Field(alias="VERIFIER_SERVER_PRIMARY_MODEL")
    ] = None
    verifier_server_fallback1_provider: Annotated[
        str | None, Field(alias="VERIFIER_SERVER_FALLBACK1_PROVIDER")
    ] = None
    verifier_server_fallback1_model: Annotated[
        str | None, Field(alias="VERIFIER_SERVER_FALLBACK1_MODEL")
    ] = None
    verifier_server_fallback2_provider: Annotated[
        str | None, Field(alias="VERIFIER_SERVER_FALLBACK2_PROVIDER")
    ] = None
    verifier_server_fallback2_model: Annotated[
        str | None, Field(alias="VERIFIER_SERVER_FALLBACK2_MODEL")
    ] = None
    verifier_server_fallback3_provider: Annotated[
        str | None, Field(alias="VERIFIER_SERVER_FALLBACK3_PROVIDER")
    ] = None
    verifier_server_fallback3_model: Annotated[
        str | None, Field(alias="VERIFIER_SERVER_FALLBACK3_MODEL")
    ] = None

    # --- Logging ---
    log_dir: Annotated[Path, Field(alias="LOG_DIR")] = Path("logs")
    log_level: Annotated[str, Field(alias="LOG_LEVEL")] = "INFO"
    log_console_level: Annotated[str, Field(alias="LOG_CONSOLE_LEVEL")] = "INFO"
    log_format: Annotated[str, Field(alias="LOG_FORMAT")] = "json"
    log_rotation: Annotated[str, Field(alias="LOG_ROTATION")] = "00:00"
    log_retention: Annotated[str, Field(alias="LOG_RETENTION")] = "30 days"
    log_compression: Annotated[str, Field(alias="LOG_COMPRESSION")] = "zip"
    log_mask_auth: Annotated[bool, Field(alias="LOG_MASK_AUTH")] = True
    log_http_level: Annotated[str, Field(alias="LOG_HTTP_LEVEL")] = "WARNING"
    log_split_files: Annotated[bool, Field(alias="LOG_SPLIT_FILES")] = True
    log_enable_http_file: Annotated[bool, Field(alias="LOG_ENABLE_HTTP_FILE")] = False

    @field_validator("runtime_env", mode="before")
    @classmethod
    def validate_runtime_env(cls, value: str) -> Literal["local", "server"]:
        normalized_value = str(value).strip().lower()
        if normalized_value not in {"local", "server"}:
            raise ValueError(f"Unsupported runtime_env: {normalized_value}")
        return normalized_value  # type: ignore[return-value]

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

    @field_validator("storage_sqlite_db_path", "storage_artifacts_dir", "log_dir", mode="before")
    @classmethod
    def _as_path(cls, value: str | Path) -> Path:
        if isinstance(value, Path):
            return value
        return Path(str(value))

    @field_validator(
        "ollama_local_url",
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

    @field_validator("ollama_server_url", mode="before")
    @classmethod
    def _normalize_ollama_server_url(cls, value: str | None) -> str | None:
        if value is None or value == "":
            return None
        normalized = str(value).strip()
        if not normalized:
            return None
        if not Settings._is_valid_ollama_server_url(normalized):
            return None
        return normalized

    @staticmethod
    def _is_valid_ollama_server_url(url: str) -> bool:
        if not url.startswith(("http://", "https://")):
            return False

        try:
            parsed = urlparse(url)
        except Exception:
            return False

        hostname = parsed.hostname
        if not hostname or not isinstance(hostname, str):
            return False

        invalid_hostnames = {"your-server-ip", "example.com", "localhost", "127.0.0.1", "0.0.0.0"}
        if hostname.lower() in invalid_hostnames:
            return False

        port = parsed.port
        if port is not None and (port < 1 or port > 65535):
            return False

        ipv4_pattern = re.compile(r"^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$")
        if ipv4_pattern.match(hostname):
            parts = [int(p) for p in hostname.split(".")]
            if all(0 <= p <= 255 for p in parts):
                return True

        domain_pattern = re.compile(r"^[a-zA-Z0-9.-]+\.[a-zA-Z0-9.-]+$")
        return bool(domain_pattern.match(hostname) and "." in hostname)

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

        fallback3_provider = getattr(self, f"{task_prefix}_fallback3_provider", None)
        fallback3_model = getattr(self, f"{task_prefix}_fallback3_model", None)
        if fallback3_provider and fallback3_model:
            steps.append(LlmRouteStep(provider=fallback3_provider, model=fallback3_model))

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

    @property
    def llm_last_resort(self) -> RouteCandidate:
        provider = self.llm_last_resort_provider or "ollama_local"
        model = self.llm_last_resort_model or self.ollama_model or "llama3:latest"
        return RouteCandidate(provider=provider, model=model)

    def _build_candidates_from_new_schema(
        self, task_prefix: str, branch: Literal["local", "server"]
    ) -> list[RouteCandidate]:
        candidates: list[RouteCandidate] = []

        primary_provider = getattr(self, f"{task_prefix}_{branch}_primary_provider", None)
        primary_model = getattr(self, f"{task_prefix}_{branch}_primary_model", None)
        if primary_provider and primary_model:
            candidates.append(RouteCandidate(provider=primary_provider, model=primary_model))

        for fallback_num in [1, 2, 3]:
            fallback_provider = getattr(
                self, f"{task_prefix}_{branch}_fallback{fallback_num}_provider", None
            )
            fallback_model = getattr(
                self, f"{task_prefix}_{branch}_fallback{fallback_num}_model", None
            )
            if fallback_provider and fallback_model:
                candidates.append(RouteCandidate(provider=fallback_provider, model=fallback_model))

        return candidates

    def _build_candidates_from_old_schema(self, task_prefix: str) -> list[RouteCandidate]:
        candidates: list[RouteCandidate] = []

        primary_provider = getattr(self, f"{task_prefix}_primary_provider", None)
        primary_model = getattr(self, f"{task_prefix}_primary_model", None)
        if primary_provider and primary_model:
            candidates.append(RouteCandidate(provider=primary_provider, model=primary_model))

        for fallback_num in [1, 2, 3]:
            fallback_provider = getattr(
                self, f"{task_prefix}_fallback{fallback_num}_provider", None
            )
            fallback_model = getattr(self, f"{task_prefix}_fallback{fallback_num}_model", None)
            if fallback_provider and fallback_model:
                candidates.append(RouteCandidate(provider=fallback_provider, model=fallback_model))

        return candidates

    def _has_new_schema(self, task_prefix: str) -> bool:
        local_provider = getattr(self, f"{task_prefix}_local_primary_provider", None)
        server_provider = getattr(self, f"{task_prefix}_server_primary_provider", None)
        return (local_provider is not None and local_provider != "") or (
            server_provider is not None and server_provider != ""
        )

    @property
    def llm_routes(self) -> dict[str, dict[str, list[RouteCandidate]]]:
        routes: dict[str, dict[str, list[RouteCandidate]]] = {}

        task_prefixes = ["tech", "news", "synthesis", "verifier"]
        for task_prefix in task_prefixes:
            routes[task_prefix] = {}
            routes[task_prefix]["local"] = self._build_candidates_from_new_schema(
                task_prefix, "local"
            )
            routes[task_prefix]["server"] = self._build_candidates_from_new_schema(
                task_prefix, "server"
            )

        return routes

    def get_task_candidates(self, task_name: str) -> list[RouteCandidate]:
        task_name_to_prefix = {
            "tech_analysis": "tech",
            "news_analysis": "news",
            "synthesis": "synthesis",
            "verification": "verifier",
        }

        task_prefix = task_name_to_prefix.get(task_name)
        if not task_prefix:
            return []

        if self._has_new_schema(task_prefix):
            branch = self.runtime_env
            return self._build_candidates_from_new_schema(task_prefix, branch)

        return self._build_candidates_from_old_schema(task_prefix)

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
