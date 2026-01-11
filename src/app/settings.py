from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import List

from pydantic import BaseModel
from pydantic import Field
from pydantic import field_validator
from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict


class OandaSettings(BaseModel):
    api_key: str = Field(default="", description="OANDA API key")
    account_id: str = Field(default="", description="OANDA account id")
    base_url: str = Field(
        default="https://api-fxpractice.oanda.com",
        description="OANDA REST API base url",
    )


class TwelveDataSettings(BaseModel):
    api_key: str = Field(default="", description="Twelve Data API key")
    base_url: str = Field(
        default="https://api.twelvedata.com",
        description="Twelve Data REST API base url",
    )


class GdeltSettings(BaseModel):
    base_url: str = Field(
        default="https://api.gdeltproject.org",
        description="GDELT API base url",
    )


class NewsApiSettings(BaseModel):
    api_key: str = Field(default="", description="NewsAPI key")
    base_url: str = Field(
        default="https://newsapi.org",
        description="NewsAPI base url",
    )


class OllamaSettings(BaseModel):
    base_url: str = Field(
        default="http://localhost:11434",
        description="Ollama server base url",
    )
    model: str = Field(default="", description="Default Ollama model name")


class StorageSettings(BaseModel):
    sqlite_db_path: Path = Field(
        default=Path("db/forex_research_assistant.sqlite3"),
        description="Path to SQLite database file",
    )
    artifacts_dir: Path = Field(
        default=Path("artifacts"),
        description="Artifacts output directory",
    )


class RuntimeSettings(BaseModel):
    mvp_symbols_raw: str = Field(
        default="EURUSD,GBPUSD,USDJPY",
        description="Comma-separated symbols list",
    )
    mvp_timeframe: str = Field(default="1m", description="Default timeframe for MVP")
    mvp_expiry_seconds: int = Field(default=60, description="Default expiry in seconds")

    llm_enabled: bool = Field(default=False, description="Enable LLM calls")
    llm_call_interval_seconds: int = Field(
        default=300,
        description="Minimum seconds between LLM calls per symbol",
    )

    news_refresh_interval_seconds: int = Field(
        default=300,
        description="Seconds between news refresh",
    )

    market_data_window_candles: int = Field(
        default=300,
        description="How many candles to keep for features",
    )

    @field_validator("mvp_timeframe")
    @classmethod
    def validate_timeframe(cls, value: str) -> str:
        normalized_value = value.strip().lower()
        allowed_values = {"1m", "5m", "15m", "30m", "1h", "4h", "1d"}
        if normalized_value not in allowed_values:
            raise ValueError(f"Unsupported timeframe: {value}")
        return normalized_value

    @field_validator("mvp_expiry_seconds", "llm_call_interval_seconds", "news_refresh_interval_seconds")
    @classmethod
    def validate_positive_seconds(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("Seconds value must be positive")
        return value

    @field_validator("market_data_window_candles")
    @classmethod
    def validate_market_data_window(cls, value: int) -> int:
        if value < 50:
            raise ValueError("market_data_window_candles must be at least 50")
        return value

    def mvp_symbols(self) -> List[str]:
        raw_parts = self.mvp_symbols_raw.split(",")
        normalized_symbols: List[str] = []
        for part in raw_parts:
            cleaned_value = part.strip().upper()
            if not cleaned_value:
                continue
            normalized_symbols.append(cleaned_value)
        if not normalized_symbols:
            raise ValueError("MVP_SYMBOLS is empty after parsing")
        return normalized_symbols


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_env: str = Field(default="development", validation_alias="APP_ENV")
    app_timezone: str = Field(default="Asia/Yerevan", validation_alias="APP_TIMEZONE")

    oanda: OandaSettings = Field(default_factory=OandaSettings)
    twelve_data: TwelveDataSettings = Field(default_factory=TwelveDataSettings)
    gdelt: GdeltSettings = Field(default_factory=GdeltSettings)
    newsapi: NewsApiSettings = Field(default_factory=NewsApiSettings)
    ollama: OllamaSettings = Field(default_factory=OllamaSettings)
    storage: StorageSettings = Field(default_factory=StorageSettings)
    runtime: RuntimeSettings = Field(default_factory=RuntimeSettings)

    def is_development(self) -> bool:
        return self.app_env.strip().lower() == "development"


@lru_cache(maxsize=1)
def get_settings() -> AppSettings:
    oanda = OandaSettings(
        api_key=AppSettings().model_fields["oanda"].default.api_key,
        account_id=AppSettings().model_fields["oanda"].default.account_id,
        base_url=AppSettings().model_fields["oanda"].default.base_url,
    )
    twelve_data = TwelveDataSettings(
        api_key=AppSettings().model_fields["twelve_data"].default.api_key,
        base_url=AppSettings().model_fields["twelve_data"].default.base_url,
    )
    gdelt = GdeltSettings(
        base_url=AppSettings().model_fields["gdelt"].default.base_url,
    )
    newsapi = NewsApiSettings(
        api_key=AppSettings().model_fields["newsapi"].default.api_key,
        base_url=AppSettings().model_fields["newsapi"].default.base_url,
    )
    ollama = OllamaSettings(
        base_url=AppSettings().model_fields["ollama"].default.base_url,
        model=AppSettings().model_fields["ollama"].default.model,
    )
    storage = StorageSettings(
        sqlite_db_path=AppSettings().model_fields["storage"].default.sqlite_db_path,
        artifacts_dir=AppSettings().model_fields["storage"].default.artifacts_dir,
    )
    runtime = RuntimeSettings(
        mvp_symbols_raw=AppSettings().model_fields["runtime"].default.mvp_symbols_raw,
        mvp_timeframe=AppSettings().model_fields["runtime"].default.mvp_timeframe,
        mvp_expiry_seconds=AppSettings().model_fields["runtime"].default.mvp_expiry_seconds,
        llm_enabled=AppSettings().model_fields["runtime"].default.llm_enabled,
        llm_call_interval_seconds=AppSettings().model_fields["runtime"].default.llm_call_interval_seconds,
        news_refresh_interval_seconds=AppSettings().model_fields["runtime"].default.news_refresh_interval_seconds,
        market_data_window_candles=AppSettings().model_fields["runtime"].default.market_data_window_candles,
    )

    settings = AppSettings(
        oanda=oanda,
        twelve_data=twelve_data,
        gdelt=gdelt,
        newsapi=newsapi,
        ollama=ollama,
        storage=storage,
        runtime=runtime,
    )
    return settings