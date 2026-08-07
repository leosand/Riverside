"""Tests API / API integration tests (TestClient, sans réseau ni DB)."""
from fastapi.testclient import TestClient

from src.api.main import app

client = TestClient(app)


def test_health() -> None:
    r = client.get("/health")
    assert r.status_code == 200 and r.json()["status"] == "ok"


def test_evaluate_alert_critical_without_db_still_200() -> None:
    # Persistance best-effort : sans DB, l'évaluation répond quand même
    r = client.post(
        "/api/v1/alerts/evaluate",
        json={"aoi_id": "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb", "ndvi_mean": 0.20, "threshold": 0.30},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["should_alert"] is True and body["severity"] == "critical"
    assert body["alert_id"] is None and body["notified"] is False


def test_evaluate_no_alert() -> None:
    r = client.post(
        "/api/v1/alerts/evaluate",
        json={"aoi_id": "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb", "ndvi_mean": 0.55, "threshold": 0.30},
    )
    assert r.status_code == 200
    assert r.json()["should_alert"] is False


def test_open_alerts_db_unavailable_returns_503_rfc7807() -> None:
    r = client.get("/api/v1/alerts/open")
    assert r.status_code == 503
    assert r.headers["content-type"].startswith("application/problem+json")


def test_scenes_invalid_bbox_rfc7807() -> None:
    r = client.get(
        "/api/v1/scenes",
        params={"bbox": "1,2,3", "start": "2026-01-01", "end": "2026-02-01"},
    )
    assert r.status_code == 400
    assert r.headers["content-type"].startswith("application/problem+json")
