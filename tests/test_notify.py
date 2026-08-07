"""Tests notification n8n — aucun appel réseau / no network calls."""
from src.alerts.notify import notify_n8n


def test_notify_disabled_when_no_url() -> None:
    assert notify_n8n(None, {"metric": "ndvi_mean"}) is False


def test_notify_disabled_empty_url() -> None:
    assert notify_n8n("", {"metric": "ndvi_mean"}) is False
