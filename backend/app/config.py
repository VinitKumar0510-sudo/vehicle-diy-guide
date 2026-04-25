from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    anthropic_api_key: str
    database_url: str = "postgresql+asyncpg://diy:diy@localhost:5433/vehicle_diy"
    redis_url: str = "redis://localhost:6379/0"

    tavily_api_key: str = ""
    reddit_client_id: str = ""
    reddit_client_secret: str = ""
    reddit_user_agent: str = "VehicleDIYBot/1.0"
    youtube_api_key: str = ""

    log_level: str = "INFO"
    environment: str = "development"

    claude_model: str = "claude-sonnet-4-6"        # guide synthesis — keep Sonnet
    claude_chat_model: str = "claude-haiku-4-5-20251001"   # intent + session chat — Haiku
    claude_vision_model: str = "claude-sonnet-4-6"  # diagram processing — keep Sonnet

    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache
def get_settings() -> Settings:
    return Settings()
