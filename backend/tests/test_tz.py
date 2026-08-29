from __future__ import annotations

from datetime import datetime

import pytest

from app.core import tz


def test_validate_accepts_an_iana_name() -> None:
    assert tz.validate("Europe/London") == "Europe/London"


def test_validate_rejects_garbage() -> None:
    with pytest.raises(ValueError, match="unknown timezone"):
        tz.validate("Not/AZone")


def test_local_date_crosses_midnight() -> None:
    # 04:00 UTC on the 10th is still the 9th in Chicago (UTC-6/-5).
    dt = datetime(2026, 3, 10, 4, 0)
    assert tz.local_date(dt, "America/Chicago").isoformat() == "2026-03-09"
    assert tz.local_date(dt, "UTC").isoformat() == "2026-03-10"
