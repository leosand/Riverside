"""Tests logique d'alerte / threshold alerting unit tests."""
from src.alerts.thresholds import evaluate_ndvi


def test_above_threshold_no_alert() -> None:
    d = evaluate_ndvi(0.45, 0.30)
    assert not d.should_alert and d.severity == "info"


def test_below_threshold_warning() -> None:
    d = evaluate_ndvi(0.27, 0.30)
    assert d.should_alert and d.severity == "warning"


def test_far_below_threshold_critical() -> None:
    d = evaluate_ndvi(0.20, 0.30)  # < 80% du seuil
    assert d.should_alert and d.severity == "critical"
