"""Tests API / API integration tests (TestClient, sans réseau)."""
from fastapi.testclient import TestClient

from src.api.main import app

client = TestClient(app)


def test_health() -> None:
    r = client.get("/health")
    assert r.status_code == 200 and r.json()["status"] == "ok"


def test_evaluate_alert_critical() -> None:
    r = client.post(
        "/api/v1/alerts/evaluate",
        json={"aoi_id": "demo", "ndvi_mean": 0.20, "threshold": 0.30},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["should_alert"] is True and body["severity"] == "critical"


def test_scenes_invalid_bbox_rfc7807() -> None:
    r = client.get(
        "/api/v1/scenes",
        params={"bbox": "1,2,3", "start": "2026-01-01", "end": "2026-02-01"},
    )
    assert r.status_code == 400
    assert r.headers["content-type"].startswith("application/problem+json")
