from functools import lru_cache

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "HybridAIAutomation API"
    app_env: str = Field(default="dev", validation_alias=AliasChoices("APP_ENV", "ENV"))
    api_prefix: str = "/api/v1"
    default_ai_provider: str = "local"

    openai_api_key: str | None = None
    openai_model: str = "gpt-5.4-mini"

    oci_config_path: str | None = None
    oci_profile: str = "DEFAULT"
    oci_ai_endpoint: str | None = None
    oci_ai_api_key: str | None = None
    oci_ai_model: str = "cohere.command-r-16k"

    oracle_db_dsn: str | None = None
    oracle_db_user: str | None = None
    oracle_db_password: str | None = None
    vector_db_url: str = "postgresql://postgres:postgres@db:5432/vector"

    jwt_secret: str = "supersecret"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    auth_required: bool = False
    demo_admin_user: str = "demo-admin"
    demo_admin_password: str = "demo-password"

    audit_log_path: str = "data/audit_events.jsonl"
    credential_store_path: str = "data/credential_store.json"

    cors_origins: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:5401",
            "http://127.0.0.1:5401",
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
