"""Routeur série NDVI — expose l'évolution temporelle d'une AOI.

EN: NDVI time-series router. Exposes the historical NDVI series of an AOI to
the dashboard (graphique « Évolution NDVI »). Lit la table ndvi_series (source
de vérité : migration 001) — contrairement au fichier statique de mise en page.
"""
from __future__ import annotations

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
    limit: Annotated[int, Query(ge=1, le=1000)] = 100,
) -> dict[str, Any]:
    """Série temporelle NDVI d'une AOI, ordre chronologique.

    EN: Chronological NDVI series for one AOI. 404 si aucune donnée.
    """
    engine = get_engine()
    with engine.connect() as conn:
        rows = conn.execute(
            text(
                "SELECT observed_at, ndvi_mean, ndvi_p10, ndvi_p90, ndwi_mean "
                "FROM ndvi_series WHERE aoi_id = :a "
                "ORDER BY observed_at ASC LIMIT :limit"
            ),
            {"a": str(aoi_id), "limit": limit},
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
            f"Aucune série NDVI pour {aoi_id} / no NDVI series found — "
            "lancez l'ingestion réelle (STAC → NDVI → ndvi_series)"
        )

    log.info("ndvi_series_served", aoi=str(aoi_id), n=len(points))
    return {
        "aoi_id": str(aoi_id),
        "threshold": settings.ndvi_alert_threshold,
        "count": len(points),
        "series": points,
    }
