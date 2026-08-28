from __future__ import annotations

import pytest

from app.core.config import DEV_JWT_SECRET, Settings


def test_dev_defaults_are_usable() -> None:
    settings = Settings()
    assert settings.database_url.startswith("sqlite")
    assert not settings.is_production


def test_production_rejects_the_default_secret() -> None:
    with pytest.raises(ValueError, match="JWT_SECRET"):
        Settings(environment="production", jwt_secret=DEV_JWT_SECRET)


def test_production_rejects_a_short_secret() -> None:
    with pytest.raises(ValueError, match="JWT_SECRET"):
        Settings(environment="production", jwt_secret="too-short")


def test_production_accepts_a_strong_secret() -> None:
    settings = Settings(environment="production", jwt_secret="s" * 40)
    assert settings.is_production
