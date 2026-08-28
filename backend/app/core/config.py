from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

# Obviously-not-production placeholder, kept >= 32 bytes so HMAC-SHA256 is happy.
DEV_JWT_SECRET = "dev-only-change-me-dev-only-change-me-0000"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    environment: str = "development"

    # Local dev defaults are zero-setup: a SQLite file and an in-process
    # fake Redis. Compose, CI, and production override both with real URLs.
    database_url: str = "sqlite:///./lifeos.db"
    redis_url: str = "fakeredis://"

    # Celery. Dev/tests run tasks synchronously (no broker/worker needed);
    # Compose sets celery_eager=false and points at a real Redis broker.
    celery_eager: bool = True
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"

    # AI assistant. Empty key -> the /coach endpoint returns 503.
    anthropic_api_key: str = ""
    assistant_model: str = "claude-opus-5"

    # Auth
    jwt_secret: str = DEV_JWT_SECRET
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 14

    # Comma-separated list in the CORS_ORIGINS env var
    cors_origins: str = "http://localhost:5173"

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"

    def model_post_init(self, context: object, /) -> None:
        if self.is_production and (
            self.jwt_secret == DEV_JWT_SECRET or len(self.jwt_secret) < 32
        ):
            raise ValueError(
                "JWT_SECRET must be a strong value (>= 32 chars) when ENVIRONMENT=production"
            )


@lru_cache
def get_settings() -> Settings:
    return Settings()
