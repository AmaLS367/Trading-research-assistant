from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Annotated, List

from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # --- Application ---
    app_env: Annotated[str, Field(alias="APP_ENV")] = "development"
    app_timezone: Annotated[str, Field(alias="APP_TIMEZONE")] = "Asia/Yerevan"

    # --- OANDA API ---
    oanda_api_key: Annotated[str, Field(alias="OANDA_API_KEY")] = ""
    oanda_account_id: Annotated[str, Field(alias="OANDA_ACCOUNT_ID")] = ""
    oanda_base_url: Annotated[str, Field(alias="OANDA_BASE_URL")] = "https://api-fxpractice.oanda.com"

    # --- Twelve Data API ---
    twelve_data_api_key: Annotated[str, Field(alias="TWELVE_DATA_API_KEY")] = ""
    twelve_data_base_url: Annotated[str, Field(alias="TWELVE_DATA_BASE_URL")] = "https://api.twelvedata.com"

    # --- GDELT API ---
    gdelt_base_url: Annotated[str, Field(alias="GDELT_BASE_URL")] = "https://api.gdeltproject.org"

    # --- NewsAPI ---
    newsapi_api_key: Annotated[str, Field(alias="NEWSAPI_API_KEY")] = ""
    newsapi_base_url: Annotated[str, Field(alias="NEWSAPI_BASE_URL")] = "https://newsapi.org"

    # --- Ollama ---
    ollama_base_url: Annotated[str, Field(alias="OLLAMA_BASE_URL")] = "http://localhost:11434"
    ollama_model: Annotated[str, Field(alias="OLLAMA_MODEL")] = ""

    # --- Storage ---
    storage_sqlite_db_path: Annotated[Path, Field(alias="STORAGE_SQLITE_DB_PATH")] = Path("db/forex_research_assistant.sqlite3")
    storage_artifacts_dir: Annotated[Path, Field(alias="STORAGE_ARTIFACTS_DIR")] = Path("artifacts")
    storage_migration_path: Annotated[str, Field(alias="STORAGE_MIGRATION_PATH")] = "src/storage/sqlite/migrations/0001_init.sql"

    # --- Runtime ---
    runtime_mvp_symbols_raw: Annotated[str, Field(alias="RUNTIME_MVP_SYMBOLS_RAW")] = "EURUSD,GBPUSD,USDJPY"
    runtime_mvp_timeframe: Annotated[str, Field(alias="RUNTIME_MVP_TIMEFRAME")] = "1m"
    runtime_mvp_expiry_seconds: Annotated[int, Field(alias="RUNTIME_MVP_EXPIRY_SECONDS")] = 60
    runtime_llm_enabled: Annotated[bool, Field(alias="RUNTIME_LLM_ENABLED")] = False
    runtime_llm_call_interval_seconds: Annotated[int, Field(alias="RUNTIME_LLM_CALL_INTERVAL_SECONDS")] = 300
    runtime_news_refresh_interval_seconds: Annotated[int, Field(alias="RUNTIME_NEWS_REFRESH_INTERVAL_SECONDS")] = 300
    runtime_market_data_window_candles: Annotated[int, Field(alias="RUNTIME_MARKET_DATA_WINDOW_CANDLES")] = 300

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

    def mvp_symbols(self) -> List[str]:
        raw_parts = self.runtime_mvp_symbols_raw.split(",")
        normalized_symbols: List[str] = []
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
