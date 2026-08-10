"""Tests export dashboard JSON — SQLite in-memory / offline."""
import json

import pytest
from sqlalchemy import create_engine, text

from src.pipeline.export_dashboard import build_dashboard_payload, export_ndvi_json

_DDL = """
CREATE TABLE ndvi_series (
    aoi_id TEXT, observed_at DATE, ndvi_mean REAL,
    ndvi_p10 REAL, ndvi_p90 REAL, ndwi_mean REAL,
    PRIMARY KEY (aoi_id, observed_at)
)
"""


def _engine():
    engine = create_engine("sqlite:///:memory:")
    with engine.begin() as conn:
        conn.execute(text(_DDL))
        conn.execute(
            text(
                "INSERT INTO ndvi_series VALUES "
                "('a1', '2026-07-01', 0.52, 0.4, 0.6, -0.1),"
                "('a1', '2026-07-11', 0.58, 0.45, 0.65, -0.08)"
            )
        )
    return engine


def test_payload_schema_and_order() -> None:
    payload = build_dashboard_payload(_engine(), "a1", 0.30)
    assert payload["meta"]["source"] == "pipeline"
    assert payload["threshold"] == 0.30
    assert [p["date"] for p in payload["series"]] == ["2026-07-01", "2026-07-11"]
    assert payload["series"][0]["ndvi_mean"] == pytest.approx(0.52)


def test_empty_series_raises() -> None:
    with pytest.raises(ValueError, match="empty|Aucune"):
        build_dashboard_payload(_engine(), "inconnu", 0.30)


def test_export_writes_json_file(tmp_path) -> None:
    out = tmp_path / "data" / "ndvi-real.json"
    path = export_ndvi_json(_engine(), "a1", out)
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["meta"]["aoi_id"] == "a1"
    assert len(payload["series"]) == 2
