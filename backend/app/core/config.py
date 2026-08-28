from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

# Obviously-not-production placeholder, kept >= 32 bytes so HMAC-SHA256 is happy.
DEV_JWT_SECRET = "dev-only-change-me-dev-only-change-me-0000"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    environment: str = "development"

    # Local dev defaults to a zero-setup SQLite file. Docker Compose, CI, and
    # production all override this with a real Postgres URL.
    database_url: str = "sqlite:///./lifeos.db"
    redis_url: str = "redis://localhost:6379/0"

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
