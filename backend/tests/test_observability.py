from __future__ import annotations

import json
import logging

from fastapi.testclient import TestClient

from app.core.observability import (
    JsonFormatter,
    init_sentry,
    request_id_ctx,
)
from app.realtime.fanout import _should_deliver


def test_request_id_is_minted_and_echoed(client: TestClient) -> None:
    resp = client.get("/api/health")
    rid = resp.headers.get("x-request-id")
    assert rid and len(rid) >= 8


def test_request_id_honours_inbound_header(client: TestClient) -> None:
    resp = client.get("/api/health", headers={"X-Request-ID": "abc123-trace"})
    assert resp.headers["x-request-id"] == "abc123-trace"


def test_metrics_endpoint_exposes_prometheus_text(client: TestClient) -> None:
    client.get("/api/health")  # generate at least one sample
    resp = client.get("/metrics")
    assert resp.status_code == 200
    assert "text/plain" in resp.headers["content-type"]
    body = resp.text
    assert "lifeos_http_requests_total" in body
    assert "lifeos_http_request_duration_seconds" in body
    # /metrics must not measure itself
    assert 'path="/metrics"' not in body


def test_readiness_probe_reports_each_dependency(client: TestClient) -> None:
    resp = client.get("/api/health/ready")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ready"
    assert body["checks"] == {"database": "ok", "redis": "ok"}


def test_json_formatter_emits_parseable_lines() -> None:
    token = request_id_ctx.set("req-42")
    try:
        record = logging.LogRecord(
            "lifeos", logging.INFO, __file__, 1, "hello", (), None
        )
        record.path = "/api/thing"
        parsed = json.loads(JsonFormatter().format(record))
    finally:
        request_id_ctx.reset(token)

    assert parsed["msg"] == "hello"
    assert parsed["level"] == "INFO"
    assert parsed["request_id"] == "req-42"
    assert parsed["path"] == "/api/thing"


def test_sentry_is_a_noop_without_a_dsn() -> None:
    assert init_sentry("", environment="test", traces_sample_rate=0.0) is False


def test_fanout_skips_own_frames_and_malformed_ones() -> None:
    assert _should_deliver({"user_id": 1, "event": {"type": "x"}, "origin": "other"}, "me")
    assert not _should_deliver({"user_id": 1, "event": {}, "origin": "me"}, "me")
    assert not _should_deliver({"user_id": 1}, "me")
    assert not _should_deliver({"event": {"type": "x"}, "origin": "other"}, "me")
