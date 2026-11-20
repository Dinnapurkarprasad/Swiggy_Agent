"""Typed application settings loaded from environment variables / `.env`.

Secrets are `SecretStr` so they never show up in reprs, logs or tracebacks.
"""

from functools import lru_cache

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.models.enums import LLMProvider, SwiggyMode


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # App
    app_env: str = "local"
    log_level: str = "INFO"
    frontend_origin: str = "http://localhost:3000"

    # Database (async SQLAlchemy URL, e.g. postgresql+asyncpg://user:pass@host:5432/db)
    database_url: SecretStr = SecretStr(
        "postgresql+asyncpg://postgres:postgres@localhost:5432/swiggy_party"
    )

    # Host sign-in with Google. The client id is public; it is not the Gemini API key.
    google_oauth_client_id: str | None = None
    # Signs our own login cookie. Changing it logs every host out.
    session_secret: SecretStr | None = None
    session_days: int = 7

    # Swiggy
    swiggy_mode: SwiggyMode = SwiggyMode.MOCK
    swiggy_mcp_url: str = "https://mcp.swiggy.com/food"
    swiggy_oauth_client_id: str | None = None
    swiggy_oauth_client_secret: SecretStr | None = None
    swiggy_oauth_redirect_uri: str = "http://localhost:8000/swiggy/oauth/callback"

    # Encrypts Swiggy OAuth tokens at rest. Required outside mock mode.
    token_encryption_key: SecretStr | None = None

    # LLM
    llm_provider: LLMProvider = LLMProvider.GEMINI
    google_api_key: SecretStr | None = None


@lru_cache
def get_settings() -> Settings:
    return Settings()
