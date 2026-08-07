"""Alertes seuils réglementaires CSR / regulatory threshold alerting.

EN: Pure decision logic — given an NDVI observation and thresholds, decide
whether to raise an alert and at which severity. Persistence is done by the API.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AlertDecision:
    should_alert: bool
    severity: str  # 'info' | 'warning' | 'critical'
    metric: str
    value: float
    threshold: float


def evaluate_ndvi(ndvi_mean: float, threshold: float) -> AlertDecision:
    """Règle MVP : NDVI moyen sous le seuil réglementaire → alerte.

    EN: MVP rule — mean NDVI below the regulatory threshold triggers an alert.
    Severity: critical if < 80% of threshold, warning otherwise.
    """
    if ndvi_mean >= threshold:
        return AlertDecision(False, "info", "ndvi_mean", ndvi_mean, threshold)
    severity = "critical" if ndvi_mean < 0.8 * threshold else "warning"
    return AlertDecision(True, severity, "ndvi_mean", ndvi_mean, threshold)
