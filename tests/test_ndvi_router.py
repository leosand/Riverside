"""Tests de l'endpoint série NDVI / NDVI series endpoint tests (SQLite in-memory)."""
from datetime import date

from fastapi.testclient import TestClient

from src.api.main import app
from src.config import settings
from src.db.session import get_engine
from src.pipeline.repository import metadata, save_ndvi_series

AOI = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"


def _with_series(tmp_path, monkeypatch) -> None:
    url = f"sqlite:///{tmp_path}/ndvi_api.db"
    monkeypatch.setattr(settings, "database_url", url)
    get_engine.cache_clear()
    engine = get_engine()
    metadata.create_all(engine)
    save_ndvi_series(
        engine,
        AOI,
        date(2026, 7, 1),
        {"ndvi_mean": 0.42, "ndvi_p10": 0.28, "ndvi_p90": 0.55},
    )
    save_ndvi_series(
        engine,
        AOI,
        date(2026, 7, 15),
        {"ndvi_mean": 0.58, "ndvi_p10": 0.41, "ndvi_p90": 0.69},
    )


def test_ndvi_series_returns_points(tmp_path, monkeypatch) -> None:
    _with_series(tmp_path, monkeypatch)
    client = TestClient(app)
    r = client.get(f"/api/v1/ndvi/series?aoi_id={AOI}")
    assert r.status_code == 200
    body = r.json()
    assert body["count"] == 2
    assert body["threshold"] == settings.ndvi_alert_threshold
    # Ordre chronologique
    assert body["series"][0]["date"] == "2026-07-01"
    assert body["series"][1]["date"] == "2026-07-15"
    assert body["series"][1]["ndvi_mean"] == 0.58


def test_ndvi_series_empty_raises_400(tmp_path, monkeypatch) -> None:
    url = f"sqlite:///{tmp_path}/ndvi_empty.db"
    monkeypatch.setattr(settings, "database_url", url)
    get_engine.cache_clear()
    engine = get_engine()
    metadata.create_all(engine)  # table vide

    client = TestClient(app)
    r = client.get(f"/api/v1/ndvi/series?aoi_id={AOI}")
    assert r.status_code == 400
    assert "Aucune série" in r.json()["detail"]


def test_ndvi_series_invalid_uuid_422(tmp_path, monkeypatch) -> None:
    client = TestClient(app)
    r = client.get("/api/v1/ndvi/series?aoi_id=pas-un-uuid")
    assert r.status_code == 422  # validation pydantic UUID
