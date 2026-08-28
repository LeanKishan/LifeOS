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

    # Hardening knobs
    max_body_bytes: int = 4 * 1024 * 1024
    global_rate_limit_per_minute: int = 600

    # Observability
    log_level: str = "INFO"
    log_json: bool = False  # prod images set true; dev keeps human-readable logs
    metrics_enabled: bool = True
    sentry_dsn: str = ""  # empty -> error tracking is a no-op
    sentry_traces_sample_rate: float = 0.0
    # WebSocket fan-out across processes. Off for the in-process fake (its
    # pub/sub consumer blocks); real Redis in Compose/prod turns it on.
    ws_fanout_enabled: bool = True

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"

    def model_post_init(self, context: object, /) -> None:
        if not self.is_production:
            return
        problems: list[str] = []
        if self.jwt_secret == DEV_JWT_SECRET or len(self.jwt_secret) < 32:
            problems.append("JWT_SECRET must be a strong value (>= 32 chars)")
        if self.database_url.startswith("sqlite"):
            problems.append("DATABASE_URL must be a real database, not the dev SQLite file")
        if self.redis_url.startswith("fakeredis"):
            problems.append("REDIS_URL must be a real Redis, not the in-process fake")
        if self.celery_eager:
            problems.append("CELERY_EAGER must be false so tasks run on a worker")
        if problems:
            raise ValueError(
                "Unsafe configuration for ENVIRONMENT=production: " + "; ".join(problems)
            )


@lru_cache
def get_settings() -> Settings:
    return Settings()
