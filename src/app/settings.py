from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    db_path: str = "trading_assistant.db"
    migration_path: str = "src/storage/sqlite/migrations/0001_init.sql"

    class Config:
        env_file = ".env"


settings = Settings()
