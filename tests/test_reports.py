"""Tests rapports CSR — offline, fonctions pures / pure offline tests."""
import pytest

from src.reports.csr_context import (
    SeriesPoint,
    breach_periods,
    build_csr_context,
    compliance_summary,
)
from src.reports.ollama_client import generate_narrative

POINTS = [
    SeriesPoint("2026-06-01", 0.45),
    SeriesPoint("2026-06-11", 0.25),  # sous seuil 0.30
    SeriesPoint("2026-06-21", 0.22),  # sous seuil (même période)
    SeriesPoint("2026-07-01", 0.52),
    SeriesPoint("2026-07-11", 0.28),  # nouvelle période de brèche
    SeriesPoint("2026-07-21", 0.61),
]


def test_compliance_summary_math() -> None:
    s = compliance_summary(POINTS, 0.30)
    assert s.n_observations == 6
    assert s.n_breach == 3
    assert s.pct_compliant == 50.0
    assert s.ndvi_min == 0.22 and s.ndvi_max == 0.61
    assert s.trend == pytest.approx(0.16, abs=1e-4)


def test_compliance_summary_empty_raises() -> None:
    with pytest.raises(ValueError):
        compliance_summary([], 0.30)


def test_breach_periods_consecutive_runs() -> None:
    periods = breach_periods(POINTS, 0.30)
    assert periods == [
        {"start": "2026-06-11", "end": "2026-07-01"},
        {"start": "2026-07-11", "end": "2026-07-21"},
    ]


def test_breach_periods_open_ended() -> None:
    pts = [SeriesPoint("2026-08-01", 0.20), SeriesPoint("2026-08-06", 0.25)]
    assert breach_periods(pts, 0.30) == [{"start": "2026-08-01", "end": "2026-08-06"}]


def test_build_csr_context_bilingual() -> None:
    ctx = build_csr_context("Rive nord lac Ontario", POINTS, 2, 0.30)
    assert ctx["summary"]["n_breach"] == 3
    assert ctx["n_open_alerts"] == 2
    fr, en = ctx["narrative"]["fr"], ctx["narrative"]["en"]
    assert "50.0 %" in fr and "seuil réglementaire 0.30" in fr
    assert "50.0%" in en and "regulatory threshold 0.30" in en


def test_ollama_disabled_returns_none() -> None:
    assert generate_narrative(None, {"summary": {}}) is None
    assert generate_narrative("", {"summary": {}}) is None
