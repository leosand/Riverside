"""Routeur rapports CSR — à monter dans main.py (une ligne).

EN: CSR reports router. Montage / wiring (évite de modifier main.py en aveugle) :

    from src.api.reports_router import router as reports_router
    app.include_router(reports_router)

GET /api/v1/reports/csr?aoi_id=...&aoi_name=...
  → contexte factuel FR/EN (offline) + narrative Ollama si OLLAMA_URL défini.
"""
from __future__ import annotations

import os
from typing import Annotated, Any

import structlog
from fastapi import APIRouter, Query
from sqlalchemy import text

from src.config import settings
from src.db.session import get_engine
from src.reports.csr_context import SeriesPoint, build_csr_context
from src.reports.ollama_client import generate_narrative

log = structlog.get_logger()
router = APIRouter(prefix="/api/v1/reports", tags=["reports"])


@router.get("/csr")
def csr_report(
    aoi_id: Annotated[str, Query(description="UUID de l'AOI")],
    aoi_name: Annotated[str, Query(description="Nom lisible de la zone")] = "AOI",
) -> dict[str, Any]:
    """Rapport CSR factuel bilingue + narrative LLM optionnelle.

    EN: Bilingual factual CSR report; Ollama narrative when OLLAMA_URL is set.
    """
    engine = get_engine()
    with engine.connect() as conn:
        rows = conn.execute(
            text(
                "SELECT observed_at, ndvi_mean FROM ndvi_series "
                "WHERE aoi_id = :a ORDER BY observed_at ASC"
            ),
            {"a": aoi_id},
        ).mappings().all()
        n_open = conn.execute(
            text("SELECT count(*) FROM alerts WHERE aoi_id = :a AND NOT acknowledged"),
            {"a": aoi_id},
        ).scalar_one()

    if not rows:
        raise ValueError(f"Aucune série NDVI pour {aoi_id} / no series found")

    points = [
        SeriesPoint(
            date=r["observed_at"].isoformat()
            if hasattr(r["observed_at"], "isoformat")
            else str(r["observed_at"]),
            ndvi_mean=float(r["ndvi_mean"]),
        )
        for r in rows
    ]
    context = build_csr_context(
        aoi_name, points, int(n_open), settings.ndvi_alert_threshold
    )
    narrative = generate_narrative(os.environ.get("OLLAMA_URL"), context)
    log.info("csr_report_built", aoi=aoi_id, llm=narrative is not None)
    return {"context": context, "narrative_llm": narrative}
