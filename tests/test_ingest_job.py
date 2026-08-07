"""Tests du job d'ingestion — `run_ingestion` avec mocks réseau (offline).

EN: Ingestion job tests — search_scenes/load_bands monkeypatched so the
pipeline runs fully offline (no STAC, no satellite download).
"""
from datetime import date

import numpy as np
import pytest
import xarray as xr
from sqlalchemy import create_engine

from src.alerts.repository import list_open_alerts
from src.alerts.repository import metadata as alerts_metadata
from src.ingest.stac_client import SceneSummary
from src.pipeline import ingest_job
from src.pipeline.ingest_job import IngestionReport, run_ingestion
from src.pipeline.repository import metadata as series_metadata


def _synthetic_stack() -> xr.DataArray:
    """Scène synthétique 3 dates 4x4 px, bandes red/nir/scl (déjà utilisé en E2E).

    EN: 3 dates, 4x4 px, red=2000/nir=8000, SCL=4 sauf nuages (8) à t1.
    """
    bands = ["red", "nir", "scl"]
    data = np.zeros((3, 3, 4, 4), dtype="float32")
    data[:, 0] = 2000.0  # red
    data[:, 1] = 8000.0  # nir
    data[:, 2] = 4.0     # scl = végétation
    data[1, 2, :2, :] = 8.0  # nuages moitié supérieure à t1
    return xr.DataArray(
        data,
        dims=("time", "band", "y", "x"),
        coords={"time": [0, 1, 2], "band": bands},
    )


def _scenes(n: int) -> list[SceneSummary]:
    return [
        SceneSummary(
            item_id=f"S2A-{i}",
            acquired_at=date(2026, 7, 1 + i),
            cloud_cover=float(5.0 + i),
        )
        for i in range(n)
    ]


def _engine(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path}/ingest_job.db")
    alerts_metadata.create_all(engine)
    series_metadata.create_all(engine)
    return engine


def test_run_ingestion_nominal(tmp_path, monkeypatch) -> None:
    """Cas nominal : scènes → composite → NDVI → série → pas d'alerte (NDVI 0.6 > seuil)."""
    engine = _engine(tmp_path)
    monkeypatch.setattr(ingest_job, "search_scenes", lambda *a, **k: _scenes(3))
    monkeypatch.setattr(ingest_job, "load_bands", lambda *a, **k: _synthetic_stack())

    report = run_ingestion(
        engine,
        "11111111-1111-4111-8111-111111111111",
        (0, 0, 1, 1),
        date(2026, 7, 1),
        date(2026, 7, 10),
    )

    assert isinstance(report, IngestionReport)
    assert report.scenes_used == 3
    assert report.observed_at == date(2026, 7, 3)  # max des acquired_at
    assert report.ndvi_mean == pytest.approx(0.6, abs=1e-4)
    assert report.alert_raised is False
    assert report.severity == "info"
    assert report.errors == []
    # Série persistée
    assert list_open_alerts(engine) == []


def test_run_ingestion_no_scenes(tmp_path, monkeypatch) -> None:
    """Aucune scène trouvée → rapport 'no_scenes', zéro effet de bord."""
    engine = _engine(tmp_path)
    monkeypatch.setattr(ingest_job, "search_scenes", lambda *a, **k: [])

    report = run_ingestion(
        engine,
        "22222222-2222-4222-8222-222222222222",
        (0, 0, 1, 1),
        date(2026, 7, 1),
        date(2026, 7, 10),
    )

    assert report.scenes_used == 0
    assert report.ndvi_mean is None
    assert report.alert_raised is False
    assert "no_scenes" in report.errors


def test_run_ingestion_all_cloud(tmp_path, monkeypatch) -> None:
    """Tout nuageux → summarize lève ValueError → rapport 'all_cloud'."""
    engine = _engine(tmp_path)

    def _cloudy_stack():
        stack = _synthetic_stack()
        stack.loc[{"band": "scl"}] = 8.0
        return stack

    monkeypatch.setattr(ingest_job, "search_scenes", lambda *a, **k: _scenes(2))
    monkeypatch.setattr(ingest_job, "load_bands", lambda *a, **k: _cloudy_stack())

    report = run_ingestion(
        engine,
        "33333333-3333-4333-8333-333333333333",
        (0, 0, 1, 1),
        date(2026, 7, 1),
        date(2026, 7, 10),
    )

    assert report.scenes_used == 2
    assert report.ndvi_mean is None
    assert report.alert_raised is False
    assert "all_cloud" in report.errors
