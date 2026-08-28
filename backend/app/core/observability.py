"""Logging, request-scoped IDs, Prometheus metrics, and Sentry wiring.

Deliberately framework-light: a `logging.Formatter` subclass for JSON, the
standard `prometheus_client` for metrics, and Sentry only when a DSN is set.
"""

from __future__ import annotations

import json
import logging
import sys
import time
import uuid
from contextvars import ContextVar
from typing import Any

from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Histogram,
    generate_latest,
)
from starlette.types import ASGIApp, Message, Receive, Scope, Send

# Set by the request-context middleware; every log line emitted while handling a
# request carries it, so logs and an `X-Request-ID` response header line up.
request_id_ctx: ContextVar[str] = ContextVar("request_id", default="-")


def get_request_id() -> str:
    return request_id_ctx.get()


class RequestIDMiddleware:
    """Pure-ASGI, so it sits in the same context as Starlette's error handler and
    the generated 500 can still name the request. Honours an inbound
    ``X-Request-ID`` (the ALB adds one) or mints a short id, binds it to the
    context var, and echoes it on the response.
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        headers = dict(scope.get("headers") or [])
        inbound = headers.get(b"x-request-id", b"").decode("latin-1")[:64]
        rid = inbound or uuid.uuid4().hex[:16]
        # No reset: each request runs in its own copied context.
        request_id_ctx.set(rid)

        async def send_wrapper(message: Message) -> None:
            if message["type"] == "http.response.start":
                message.setdefault("headers", [])
                message["headers"].append((b"x-request-id", rid.encode("latin-1")))
            await send(message)

        await self.app(scope, receive, send_wrapper)


# ── logging ───────────────────────────────────────────────────────────────
_RESERVED = frozenset(
    logging.LogRecord("", 0, "", 0, "", (), None).__dict__
) | {"message", "asctime", "taskName"}


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        created = time.gmtime(record.created)
        payload: dict[str, Any] = {
            "ts": f"{time.strftime('%Y-%m-%dT%H:%M:%S', created)}.{int(record.msecs):03d}Z",
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
            "request_id": request_id_ctx.get(),
        }
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        # Anything passed via logger.info(..., extra={...}).
        for key, value in record.__dict__.items():
            if key not in _RESERVED and not key.startswith("_"):
                payload.setdefault(key, value)
        return json.dumps(payload, default=str)


class TextFormatter(logging.Formatter):
    def __init__(self) -> None:
        super().__init__(
            "%(asctime)s %(levelname)-7s %(name)s [%(request_id)s] %(message)s",
            datefmt="%H:%M:%S",
        )

    def format(self, record: logging.LogRecord) -> str:
        record.request_id = request_id_ctx.get()
        return super().format(record)


def configure_logging(*, json_logs: bool, level: str) -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter() if json_logs else TextFormatter())

    root = logging.getLogger()
    root.handlers[:] = [handler]
    root.setLevel(level.upper())

    # Our request-context middleware emits one structured line per request;
    # silence uvicorn's parallel access log so there aren't two.
    access = logging.getLogger("uvicorn.access")
    access.handlers[:] = []
    access.propagate = False


# ── metrics ───────────────────────────────────────────────────────────────
HTTP_REQUESTS = Counter(
    "lifeos_http_requests_total",
    "HTTP requests by method, route template and status.",
    ["method", "path", "status"],
)
HTTP_LATENCY = Histogram(
    "lifeos_http_request_duration_seconds",
    "HTTP request latency by method and route template.",
    ["method", "path"],
)


def render_metrics() -> tuple[bytes, str]:
    return generate_latest(), CONTENT_TYPE_LATEST


# ── error tracking ────────────────────────────────────────────────────────
def init_sentry(dsn: str, *, environment: str, traces_sample_rate: float) -> bool:
    """Initialise Sentry if a DSN is configured. Returns whether it was enabled."""
    if not dsn:
        return False
    import sentry_sdk

    sentry_sdk.init(
        dsn=dsn,
        environment=environment,
        traces_sample_rate=traces_sample_rate,
        # PII off by default; the request-id tag is enough to correlate.
    )
    return True
