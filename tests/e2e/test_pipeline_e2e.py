"""E2E pipeline — scène synthétique → composite → NDVI → série → alerte.

EN: End-to-end pipeline validation with a fully synthetic xarray stack — no
network, no satellite download. Vérifie la chaîne numérique complète.
"""
from datetime import date

import numpy as np
import pytest
import xarray as xr
from sqlalchemy import create_engine

from src.alerts.repository import acknowledge_alert, list_open_alerts, save_alert
from src.alerts.repository import metadata as alerts_metadata
from src.alerts.thresholds import evaluate_ndvi
from src.cloud_removal.run_dsen2cr import temporal_median_composite
from src.indices.ndvi import compute_ndvi, summarize
from src.pipeline.repository import metadata as series_metadata
from src.pipeline.repository import save_ndvi_series


def _synthetic_stack() -> xr.DataArray:
    """3 dates, 4x4 px : red=2000/nir=8000, une date partiellement nuageuse.

    EN: dims (time, band, y, x); SCL=4 (végétation) sauf nuages (8) au t1.
    """
    times = [0, 1, 2]
    bands = ["red", "nir", "scl"]
    shape = (len(times), len(bands), 4, 4)
    data = np.zeros(shape, dtype="float32")
    data[:, 0] = 2000.0  # red
    data[:, 1] = 8000.0  # nir
    data[:, 2] = 4.0     # scl = végétation
    data[1, 2, :2, :] = 8.0  # nuages sur la moitié supérieure à t1
    return xr.DataArray(
        data,
        dims=("time", "band", "y", "x"),
        coords={"time": times, "band": bands},
    )


def test_e2e_synthetic_scene_to_alert(tmp_path) -> None:
    # 1) Composite sans nuages — le masque SCL exclut les pixels nuageux de t1
    composite = temporal_median_composite(_synthetic_stack())
    ndvi = compute_ndvi(composite["red"], composite["nir"])

    # 2) Validation numérique : NDVI connu = (0.8-0.2)/(0.8+0.2) = 0.6
    stats = summarize(ndvi)
    assert stats["ndvi_mean"] == pytest.approx(0.6, abs=1e-4)
    assert stats["ndvi_p10"] <= stats["ndvi_mean"] <= stats["ndvi_p90"]

    # 3) Persistance série (SQLite fichier / file-based, partagé entre connexions)
    engine = create_engine(f"sqlite:///{tmp_path}/e2e.db")
    alerts_metadata.create_all(engine)
    series_metadata.create_all(engine)
    save_ndvi_series(engine, "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa", date(2026, 7, 15), stats)

    # 4) Évaluation : 0.6 > seuil 0.30 → pas d'alerte
    decision = evaluate_ndvi(stats["ndvi_mean"], 0.30)
    assert decision.should_alert is False

    # 5) Scénario de brèche : NDVI dégradé → alerte critique → acquittement
    breach = evaluate_ndvi(0.20, 0.30)
    assert breach.should_alert and breach.severity == "critical"
    alert_id = save_alert(engine, "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa", breach)
    assert len(list_open_alerts(engine)) == 1
    assert acknowledge_alert(engine, alert_id) is True
    assert list_open_alerts(engine) == []


def test_e2e_all_cloud_scene_raises() -> None:
    stack = _synthetic_stack()
    stack.loc[{"band": "scl"}] = 8.0  # tout nuageux / fully cloudy
    composite = temporal_median_composite(stack)
    ndvi = compute_ndvi(composite["red"], composite["nir"])
    with pytest.raises(ValueError, match="nuageuse|cloud"):
        summarize(ndvi)
