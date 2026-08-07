"""Notification n8n — webhook HTTP avec retry + backoff.

EN: n8n webhook notification. Best-effort: failures are logged, never raised —
une alerte critique ne doit jamais faire échouer la requête API.
"""
from __future__ import annotations

from typing import Any

import httpx
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

log = structlog.get_logger()


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=8), reraise=True)
def _post(webhook_url: str, payload: dict[str, Any]) -> None:
    resp = httpx.post(webhook_url, json=payload, timeout=10.0)
    resp.raise_for_status()


def notify_n8n(webhook_url: str | None, payload: dict[str, Any]) -> bool:
    """Envoie la charge utile au webhook n8n. False si désactivé ou en échec.

    EN: Returns False when disabled (empty URL) or after retries exhausted.
    """
    if not webhook_url:
        log.info("n8n_webhook_disabled")
        return False
    try:
        _post(webhook_url, payload)
        log.info("n8n_notified", metric=payload.get("metric"))
        return True
    except httpx.HTTPError as exc:
        log.error("n8n_notify_failed", error=str(exc))
        return False
