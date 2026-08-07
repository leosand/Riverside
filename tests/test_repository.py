"""Tests persistance alertes — SQLite in-memory, sans réseau ni PostGIS.

EN: Repository tests against in-memory SQLite; FK/CHECK constraints live in
the Postgres migration and are not exercised here.
"""
from sqlalchemy import create_engine

from src.alerts.repository import alerts_table, list_open_alerts, metadata, save_alert
from src.alerts.thresholds import AlertDecision


def _engine():
    engine = create_engine("sqlite:///:memory:")
    metadata.create_all(engine)
    return engine


def _decision(severity: str = "critical") -> AlertDecision:
    return AlertDecision(True, severity, "ndvi_mean", 0.20, 0.30)


def test_save_and_list_open_alerts() -> None:
    engine = _engine()
    alert_id = save_alert(engine, "aoi-1", _decision())
    rows = list_open_alerts(engine)
    assert len(rows) == 1
    assert rows[0]["id"] == alert_id
    assert rows[0]["severity"] == "critical"
    assert rows[0]["acknowledged"] is False


def test_list_open_alerts_filter_by_aoi() -> None:
    engine = _engine()
    save_alert(engine, "aoi-1", _decision())
    save_alert(engine, "aoi-2", _decision("warning"))
    rows = list_open_alerts(engine, aoi_id="aoi-1")
    assert len(rows) == 1 and rows[0]["aoi_id"] == "aoi-1"


def test_table_matches_migration_columns() -> None:
    # Garde-fou de dérive schéma / schema drift guard vs 001_init.sql
    expected = {
        "id", "aoi_id", "raised_at", "metric",
        "value", "threshold", "severity", "acknowledged",
    }
    assert expected == set(alerts_table.c.keys())
