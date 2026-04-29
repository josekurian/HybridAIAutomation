from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "HybridAIAutomation API"
    app_env: str = "local"
    api_prefix: str = "/api/v1"
    default_ai_provider: str = "local"

    openai_api_key: str | None = None
    openai_model: str = "gpt-5.4-mini"

    oci_ai_endpoint: str | None = None
    oci_ai_api_key: str | None = None
    oci_ai_model: str = "cohere.command-r-16k"

    cors_origins: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ]
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
