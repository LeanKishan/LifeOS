from __future__ import annotations

import pytest

from app.core.config import DEV_JWT_SECRET, Settings

# A production config that passes every guard, for tests that tweak one field.
PROD_OK = {
    "environment": "production",
    "jwt_secret": "s" * 40,
    "database_url": "postgresql+psycopg://u:p@db/lifeos",
    "redis_url": "redis://redis:6379/0",
    "celery_eager": False,
}


def test_dev_defaults_are_usable(monkeypatch: pytest.MonkeyPatch) -> None:
    # CI exports DATABASE_URL / REDIS_URL for the real services; this test is
    # about the built-in zero-setup defaults, so clear the environment first.
    for var in ("DATABASE_URL", "REDIS_URL", "ENVIRONMENT", "CELERY_EAGER", "JWT_SECRET"):
        monkeypatch.delenv(var, raising=False)
    settings = Settings(_env_file=None)
    assert settings.database_url.startswith("sqlite")
    assert settings.redis_url.startswith("fakeredis")
    assert not settings.is_production


def test_production_rejects_the_default_secret() -> None:
    with pytest.raises(ValueError, match="JWT_SECRET"):
        Settings(**{**PROD_OK, "jwt_secret": DEV_JWT_SECRET})


def test_production_rejects_a_short_secret() -> None:
    with pytest.raises(ValueError, match="JWT_SECRET"):
        Settings(**{**PROD_OK, "jwt_secret": "too-short"})


def test_production_rejects_dev_sqlite() -> None:
    with pytest.raises(ValueError, match="DATABASE_URL"):
        Settings(**{**PROD_OK, "database_url": "sqlite:///./lifeos.db"})


def test_production_rejects_fakeredis() -> None:
    with pytest.raises(ValueError, match="REDIS_URL"):
        Settings(**{**PROD_OK, "redis_url": "fakeredis://"})


def test_production_rejects_eager_celery() -> None:
    with pytest.raises(ValueError, match="CELERY_EAGER"):
        Settings(**{**PROD_OK, "celery_eager": True})


def test_production_accepts_a_fully_hardened_config() -> None:
    settings = Settings(**PROD_OK)
    assert settings.is_production
