"""Job d'ingestion NDVI — orchestration complète du pipeline.

EN: Scheduled ingestion job: STAC search → band stack → cloud-free composite
→ NDVI → persist series → evaluate thresholds → persist/notify alerts.
Conçu pour être appelé par un cron, n8n ou APScheduler / callable from cron,
n8n or APScheduler.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

import structlog

from src.alerts.notify import notify_n8n
from src.alerts.repository import save_alert
from src.alerts.thresholds import evaluate_ndvi
from src.cloud_removal.run_dsen2cr import temporal_median_composite
from src.config import settings
from src.indices.ndvi import compute_ndvi, summarize
from src.ingest.stac_client import load_bands, search_scenes
from src.pipeline.repository import save_ndvi_series

log = structlog.get_logger()


@dataclass(frozen=True)
class IngestionReport:
    """Compte rendu d'exécution / job execution report."""

    aoi_id: str
    scenes_used: int
    observed_at: date | None
    ndvi_mean: float | None
    alert_raised: bool
    severity: str
    errors: list[str] = field(default_factory=list)


def run_ingestion(
    engine,  # sqlalchemy.Engine — type lax pour injection en tests / DI-friendly
    aoi_id: str,
    bbox: tuple[float, float, float, float],
    start: date,
    end: date,
) -> IngestionReport:
    """Exécute le pipeline complet pour une AOI et une fenêtre temporelle.

    EN: Full pipeline run. Erreurs capturées dans le rapport / errors are
    collected in the report instead of raising (batch-friendly).
    """
    errors: list[str] = []

    scenes = search_scenes(bbox, start, end)
    if not scenes:
        log.warning("no_scenes_found", aoi=aoi_id)
        return IngestionReport(aoi_id, 0, None, None, False, "info", ["no_scenes"])

    stack = load_bands([s.item_id for s in scenes], bbox)
    composite = temporal_median_composite(stack)
    ndvi = compute_ndvi(composite["red"], composite["nir"])

    try:
        stats = summarize(ndvi)
    except ValueError as exc:
        log.warning("all_cloud_scene", aoi=aoi_id, error=str(exc))
        return IngestionReport(aoi_id, len(scenes), None, None, False, "info", ["all_cloud"])

    observed_at = max(s.acquired_at for s in scenes)
    save_ndvi_series(engine, aoi_id, observed_at, stats)

    decision = evaluate_ndvi(stats["ndvi_mean"], settings.ndvi_alert_threshold)
    alert_id: str | None = None
    if decision.should_alert:
        alert_id = save_alert(engine, aoi_id, decision)
        if decision.severity == "critical":
            notify_n8n(
                settings.n8n_webhook_url,
                {
                    "aoi_id": aoi_id,
                    "alert_id": alert_id,
                    "metric": decision.metric,
                    "value": decision.value,
                    "threshold": decision.threshold,
                    "severity": decision.severity,
                },
            )

    log.info(
        "ingestion_done",
        aoi=aoi_id,
        scenes=len(scenes),
        ndvi_mean=stats["ndvi_mean"],
        alert=decision.should_alert,
    )
    return IngestionReport(
        aoi_id=aoi_id,
        scenes_used=len(scenes),
        observed_at=observed_at,
        ndvi_mean=stats["ndvi_mean"],
        alert_raised=decision.should_alert,
        severity=decision.severity,
        errors=errors,
    )
