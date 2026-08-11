"""Routeur série NDVI — expose l'évolution temporelle d'une AOI.

EN: NDVI time-series router. Exposes the historical NDVI series of an AOI to
the dashboard (graphique « Évolution NDVI »). Lit la table ndvi_series (source
de vérité : migration 001). Fenêtre glissante : `months` limite aux N derniers
mois (défaut 12) — le dashboard s'ajuste automatiquement aux données récentes.
"""
from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Annotated, Any
from uuid import UUID

import structlog
from fastapi import APIRouter, Query
from sqlalchemy import text

from src.config import settings
from src.db.session import get_engine

log = structlog.get_logger()
router = APIRouter(prefix="/api/v1/ndvi", tags=["ndvi"])


@router.get("/series")
def ndvi_series(
    aoi_id: Annotated[UUID, Query(description="UUID de l'AOI")],
    months: Annotated[int, Query(ge=1, le=24, description="Fenêtre glissante (mois)")] = 12,
    limit: Annotated[int, Query(ge=1, le=1000)] = 200,
) -> dict[str, Any]:
    """Série temporelle NDVI d'une AOI sur les N derniers mois.

    EN: Chronological NDVI series for one AOI over the last N months (sliding
    window). 400 si aucune donnée dans la fenêtre.
    """
    engine = get_engine()
    # Fenêtre glissante : from_date = aujourd'hui (UTC) − N mois
    today = datetime.now(timezone.utc).date()
    year = today.year
    month = today.month - months
    while month <= 0:
        month += 12
        year -= 1
    from_date = date(year, month, 1)

    with engine.connect() as conn:
        rows = conn.execute(
            text(
                "SELECT observed_at, ndvi_mean, ndvi_p10, ndvi_p90, ndwi_mean "
                "FROM ndvi_series WHERE aoi_id = :a AND observed_at >= :from_date "
                "ORDER BY observed_at ASC LIMIT :limit"
            ),
            {"a": str(aoi_id), "from_date": from_date, "limit": limit},
        ).mappings().all()

    points = []
    for r in rows:
        observed = r["observed_at"]
        points.append(
            {
                "date": observed.isoformat()
                if hasattr(observed, "isoformat")
                else str(observed),
                "ndvi_mean": float(r["ndvi_mean"]),
                "ndvi_p10": float(r["ndvi_p10"]) if r["ndvi_p10"] is not None else None,
                "ndvi_p90": float(r["ndvi_p90"]) if r["ndvi_p90"] is not None else None,
                "ndwi_mean": float(r["ndwi_mean"]) if r["ndwi_mean"] is not None else None,
            }
        )

    if not points:
        raise ValueError(
            f"Aucune série NDVI pour {aoi_id} sur les {months} derniers mois "
            f"/ no NDVI series in the last {months} months — lancez l'ingestion réelle"
        )

    log.info("ndvi_series_served", aoi=str(aoi_id), n=len(points), months=months)
    return {
        "aoi_id": str(aoi_id),
        "threshold": settings.ndvi_alert_threshold,
        "months": months,
        "from_date": from_date.isoformat(),
        "count": len(points),
        "series": points,
    }
