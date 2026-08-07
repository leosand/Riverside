"""E2E API — cycle complet via TestClient avec SQLite fichier.

EN: Full API cycle: evaluate (alert) → open alerts → acknowledge → open empty.
Injecte SQLite via monkeypatch sur settings + cache_clear / DI via settings.
"""
import pytest
from fastapi.testclient import TestClient

from src.alerts.repository import metadata as alerts_metadata
from src.api.main import app
from src.config import settings
from src.db.session import get_engine


@pytest.fixture
def sqlite_db(tmp_path, monkeypatch):
    """Engine SQLite fichier injecté dans l'API / file-based SQLite injected."""
    url = f"sqlite:///{tmp_path}/api_e2e.db"
    monkeypatch.setattr(settings, "database_url", url)
    get_engine.cache_clear()
    engine = get_engine()
    alerts_metadata.create_all(engine)
    yield engine
    get_engine.cache_clear()  # restaure l'engine Postgres par défaut


def test_e2e_alert_lifecycle(sqlite_db) -> None:
    client = TestClient(app)

    # 1) Évaluation sous le seuil → alerte critique persistée
    r = client.post(
        "/api/v1/alerts/evaluate",
        json={"aoi_id": "aoi-e2e", "ndvi_mean": 0.20, "threshold": 0.30},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["should_alert"] is True and body["severity"] == "critical"
    alert_id = body["alert_id"]
    assert alert_id is not None

    # 2) L'alerte apparaît dans les ouvertes
    r = client.get("/api/v1/alerts/open", params={"aoi_id": "aoi-e2e"})
    assert r.status_code == 200 and r.json()["count"] == 1

    # 3) Acquittement
    r = client.post(f"/api/v1/alerts/{alert_id}/acknowledge")
    assert r.status_code == 200 and r.json()["acknowledged"] is True

    # 4) Plus rien d'ouvert + 404 RFC 7807 au second acquittement
    assert client.get("/api/v1/alerts/open").json()["count"] == 0
    r = client.post(f"/api/v1/alerts/{alert_id}/acknowledge")
    assert r.status_code == 404
    assert r.headers["content-type"].startswith("application/problem+json")
