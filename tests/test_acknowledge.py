"""Tests acquittement d'alertes / acknowledge unit tests (SQLite in-memory)."""
from sqlalchemy import create_engine

from src.alerts.repository import (
    acknowledge_alert,
    list_open_alerts,
    metadata,
    save_alert,
)
from src.alerts.thresholds import AlertDecision


def _engine():
    engine = create_engine("sqlite:///:memory:")
    metadata.create_all(engine)
    return engine


def _decision() -> AlertDecision:
    return AlertDecision(True, "critical", "ndvi_mean", 0.20, 0.30)


def test_acknowledge_removes_from_open_list() -> None:
    engine = _engine()
    alert_id = save_alert(engine, "cccccccc-cccc-4ccc-8ccc-cccccccccccc", _decision())
    assert acknowledge_alert(engine, alert_id) is True
    assert list_open_alerts(engine) == []


def test_acknowledge_unknown_returns_false() -> None:
    engine = _engine()
    assert acknowledge_alert(engine, "inexistant") is False


def test_acknowledge_twice_returns_false() -> None:
    engine = _engine()
    alert_id = save_alert(engine, "cccccccc-cccc-4ccc-8ccc-cccccccccccc", _decision())
    assert acknowledge_alert(engine, alert_id) is True
    assert acknowledge_alert(engine, alert_id) is False
