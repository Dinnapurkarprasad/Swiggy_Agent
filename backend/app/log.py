"""Structured JSON logging.

Usage:
    log = get_logger(__name__)
    log.info(
        "cart updated",
        extra={"party_id": pid, "node": "place_orders", "tool": "update_food_cart"},
    )

Never log tokens or guest PII (names, phone numbers, addresses).
"""

import json
import logging
import sys
from datetime import UTC, datetime

# Only these `extra` keys are emitted, so arbitrary payloads can't leak into logs by accident.
_ALLOWED_EXTRA = ("party_id", "node", "tool", "order_id", "duration_ms", "status")


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, object] = {
            "ts": datetime.fromtimestamp(record.created, UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        for key in _ALLOWED_EXTRA:
            value = getattr(record, key, None)
            if value is not None:
                payload[key] = value
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)


def configure_logging(level: str = "INFO") -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers[:] = [handler]
    root.setLevel(level.upper())


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
