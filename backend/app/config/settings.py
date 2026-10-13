"""Application settings loaded from environment variables and .env file.

No secrets are hardcoded. All values are read from environment or .env.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.config.constants import (
    DEFAULT_HOST,
    DEFAULT_HTTP_MAX_RETRIES,
    DEFAULT_HTTP_TIMEOUT,
    DEFAULT_LOG_LEVEL,
    DEFAULT_MAX_RESPONSE_BYTES,
    DEFAULT_PORT,
    AppEnv,
    AppMode,
    LogFormat,
)


BASE_DIR = Path(__file__).resolve().parent.parent.parent  # backend/
ROOT_DIR = BASE_DIR.parent  # wp-seo-studio/
DATA_DIR = BASE_DIR / "data"


class Settings(BaseSettings):
    """Runtime settings.

    Precedence (highest to lowest):
      1. Environment variables
      2. .env file at project root
      3. Defaults declared here

    `populate_by_name=True` allows constructing with field names (db_url)
    as well as aliases (DB_URL). Tests use field names for brevity.
    """

    model_config = SettingsConfigDict(
        env_file=(ROOT_DIR / ".env", BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        populate_by_name=True,
    )

    # --- App ---------------------------------------------------------------
    app_env: AppEnv = Field(default=AppEnv.DEVELOPMENT, alias="APP_ENV")
    app_debug: bool = Field(default=False, alias="APP_DEBUG")
    app_mode: AppMode = Field(default=AppMode.MOCK, alias="APP_MODE")
    app_host: str = Field(default=DEFAULT_HOST, alias="APP_HOST")
    app_port: int = Field(default=DEFAULT_PORT, alias="APP_PORT", ge=1, le=65535)

    # --- Logging -----------------------------------------------------------
    log_level: str = Field(default=DEFAULT_LOG_LEVEL, alias="LOG_LEVEL")
    log_format: LogFormat = Field(default=LogFormat.HUMAN, alias="LOG_FORMAT")

    # --- Database ----------------------------------------------------------
    db_url: str = Field(
        default=f"sqlite+aiosqlite:///{DATA_DIR / 'app.db'}",
        alias="DB_URL",
    )

    # --- WordPress (Phase 2) ----------------------------------------------
    wp_base_url: str = Field(default="", alias="WP_BASE_URL")
    wp_username: str = Field(default="", alias="WP_USERNAME")
    wp_app_password: str = Field(default="", alias="WP_APP_PASSWORD")

    # --- WooCommerce (Phase 2) --------------------------------------------
    woo_consumer_key: str = Field(default="", alias="WOO_CONSUMER_KEY")
    woo_consumer_secret: str = Field(default="", alias="WOO_CONSUMER_SECRET")

    # --- AI (optional) -----------------------------------------------------
    ai_provider: str = Field(default="none", alias="AI_PROVIDER")
    ai_api_key: str = Field(default="", alias="AI_API_KEY")
    ai_model: str = Field(default="", alias="AI_MODEL")

    # --- Image Search (optional) ------------------------------------------
    image_search_provider: str = Field(default="none", alias="IMAGE_SEARCH_PROVIDER")
    image_search_api_key: str = Field(default="", alias="IMAGE_SEARCH_API_KEY")

    # --- HTTP --------------------------------------------------------------
    http_timeout: int = Field(default=DEFAULT_HTTP_TIMEOUT, alias="HTTP_TIMEOUT", ge=1, le=300)
    http_max_retries: int = Field(
        default=DEFAULT_HTTP_MAX_RETRIES, alias="HTTP_MAX_RETRIES", ge=0, le=10
    )
    http_max_response_bytes: int = Field(
        default=DEFAULT_MAX_RESPONSE_BYTES,
        alias="HTTP_MAX_RESPONSE_BYTES",
        ge=1024,
    )

    # --- CORS --------------------------------------------------------------
    cors_origins: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ],
        alias="CORS_ORIGINS",
    )

    # --- Validators --------------------------------------------------------

    @field_validator("log_level")
    @classmethod
    def _validate_log_level(cls, value: str) -> str:
        allowed = {"debug", "info", "warning", "error", "critical"}
        normalized = value.strip().lower()
        if normalized not in allowed:
            raise ValueError(f"LOG_LEVEL must be one of {sorted(allowed)}, got {value!r}")
        return normalized

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _parse_cors_origins(cls, value: object) -> object:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @field_validator("wp_base_url")
    @classmethod
    def _normalize_wp_base_url(cls, value: str) -> str:
        value = value.strip()
        if value and value.endswith("/"):
            value = value.rstrip("/")
        return value

    # --- Derived helpers ---------------------------------------------------

    @property
    def is_production(self) -> bool:
        return self.app_env == AppEnv.PRODUCTION

    @property
    def is_mock_mode(self) -> bool:
        return self.app_mode == AppMode.MOCK

    @property
    def effective_app_mode(self) -> AppMode:
        """In production, always use REAL mode regardless of APP_MODE."""
        if self.is_production:
            return AppMode.REAL
        return self.app_mode

    def masked_dump(self) -> dict[str, object]:
        """Return settings as dict with secrets masked for safe logging."""
        from app.core.security import mask_dict  # local import to avoid cycle

        return mask_dict(self.model_dump())


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Cached settings instance. Use FastAPI dependency injection to override in tests."""
    return Settings()