"""Contexte de rapport CSR — fonctions pures, offline, bilingues FR/EN.

EN: Pure builders computing CSR compliance context from NDVI series and
alerts. Aucune dépendance réseau / no network dependency — narrative LLM
optionnelle dans ollama_client.py.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SeriesPoint:
    """Point de série NDVI / one NDVI series point."""

    date: str  # ISO YYYY-MM-DD
    ndvi_mean: float


@dataclass(frozen=True)
class ComplianceSummary:
    """Synthèse de conformité au seuil réglementaire / compliance summary."""

    n_observations: int
    ndvi_min: float
    ndvi_max: float
    ndvi_last: float
    n_breach: int
    pct_compliant: float  # % d'observations >= seuil / share above threshold
    trend: float  # dernière - première valeur / last minus first


def compliance_summary(
    points: list[SeriesPoint], threshold: float
) -> ComplianceSummary:
    """Calcule les indicateurs de conformité / compute compliance indicators."""
    if not points:
        raise ValueError("Série vide — impossible de résumer / empty series")
    values = [p.ndvi_mean for p in points]
    n_breach = sum(1 for v in values if v < threshold)
    return ComplianceSummary(
        n_observations=len(values),
        ndvi_min=min(values),
        ndvi_max=max(values),
        ndvi_last=values[-1],
        n_breach=n_breach,
        pct_compliant=round(100.0 * (len(values) - n_breach) / len(values), 1),
        trend=round(values[-1] - values[0], 4),
    )


def breach_periods(
    points: list[SeriesPoint], threshold: float
) -> list[dict[str, str]]:
    """Périodes consécutives sous le seuil / consecutive below-threshold runs."""
    periods: list[dict[str, str]] = []
    start: str | None = None
    for p in points:
        if p.ndvi_mean < threshold and start is None:
            start = p.date
        elif p.ndvi_mean >= threshold and start is not None:
            periods.append({"start": start, "end": p.date})
            start = None
    if start is not None:
        periods.append({"start": start, "end": points[-1].date})
    return periods


def build_csr_context(
    aoi_name: str,
    points: list[SeriesPoint],
    n_open_alerts: int,
    threshold: float,
) -> dict[str, object]:
    """Assemble le contexte complet du rapport CSR FR/EN / full CSR context.

    Structure : métriques brutes + paragraphes factuels FR et EN (zéro LLM
    requis — la narrative Ollama est un bonus, jamais une dépendance).
    """
    summary = compliance_summary(points, threshold)
    periods = breach_periods(points, threshold)

    fr = (
        f"Zone {aoi_name} : {summary.n_observations} observations NDVI analysées "
        f"(seuil réglementaire {threshold:.2f}). Conformité : "
        f"{summary.pct_compliant} % des relevés au-dessus du seuil ; "
        f"{summary.n_breach} dépassement(s) détecté(s), dont "
        f"{len(periods)} période(s) continue(s). Tendance sur la période : "
        f"{'+' if summary.trend >= 0 else ''}{summary.trend:.3f}. "
        f"{n_open_alerts} alerte(s) réglementaire(s) ouverte(s)."
    )
    en = (
        f"Area {aoi_name}: {summary.n_observations} NDVI observations analysed "
        f"(regulatory threshold {threshold:.2f}). Compliance: "
        f"{summary.pct_compliant}% of readings above threshold; "
        f"{summary.n_breach} breach(es) detected across "
        f"{len(periods)} continuous period(s). Trend over period: "
        f"{'+' if summary.trend >= 0 else ''}{summary.trend:.3f}. "
        f"{n_open_alerts} open regulatory alert(s)."
    )

    return {
        "aoi_name": aoi_name,
        "threshold": threshold,
        "summary": {
            "n_observations": summary.n_observations,
            "ndvi_min": summary.ndvi_min,
            "ndvi_max": summary.ndvi_max,
            "ndvi_last": summary.ndvi_last,
            "n_breach": summary.n_breach,
            "pct_compliant": summary.pct_compliant,
            "trend": summary.trend,
        },
        "breach_periods": periods,
        "n_open_alerts": n_open_alerts,
        "narrative": {"fr": fr, "en": en},
    }
