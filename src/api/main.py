"""API Riverside — FastAPI, erreurs RFC 7807, logs JSON structurés.

EN: Riverside API — FastAPI with RFC 7807 problem details and structured logs.
Intégration EBP : endpoints REST versionnés /api/v1/* + webhook n8n (critique).
Persistance best-effort : une panne DB ne bloque jamais l'évaluation dry-run.
"""
from __future__ import annotations

from datetime import date
from typing import Any

import structlog
from fastapi import FastAPI, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy.exc import SQLAlchemyError

from src.alerts.notify import notify_n8n
from src.alerts.repository import list_open_alerts, save_alert
from src.alerts.thresholds import evaluate_ndvi
from src.config import settings
from src.db.session import get_engine
from src.ingest.stac_client import SceneSummary, search_scenes

log = structlog.get_logger()

app = FastAPI(
    title="Riverside API",
    version="0.2.0",
    description="Surveillance automatisée des berges — NDVI, alertes CSR. "
    "Automated shoreline monitoring.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins.split(","),
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"],
)


class ProblemDetail(BaseModel):
    """RFC 7807 problem+json / corps d'erreur standardisé."""

    type: str = "about:blank"
    title: str
    status: int
    detail: str


def _problem(status: int, title: str, detail: str) -> JSONResponse:
    return JSONResponse(
        status_code=status,
        media_type="application/problem+json",
        content=ProblemDetail(title=title, status=status, detail=detail).model_dump(),
    )


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError) -> JSONResponse:
    log.warning("bad_request", path=str(request.url), error=str(exc))
    return _problem(400, "Bad Request", str(exc))


@app.exception_handler(SQLAlchemyError)
async def db_error_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:
    log.error("db_unavailable", path=str(request.url), error=str(exc))
    return _problem(503, "Service Unavailable", "Base de données indisponible / database unavailable")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "riverside"}


class ScenesResponse(BaseModel):
    count: int
    scenes: list[SceneSummary]


@app.get("/api/v1/scenes", response_model=ScenesResponse)
def list_scenes(
    bbox: str = Query(..., description="minx,miny,maxx,maxy en WGS84"),
    start: date = Query(...),
    end: date = Query(...),
    max_cloud: float = Query(default=20.0, ge=0, le=100),
) -> ScenesResponse:
    """Recherche les scènes Sentinel-2 disponibles / search available scenes."""
    parts = tuple(float(v) for v in bbox.split(","))
    if len(parts) != 4:
        raise ValueError("bbox doit contenir 4 valeurs / bbox needs 4 values")
    scenes = search_scenes(parts, start, end, max_cloud)  # type: ignore[arg-type]
    return ScenesResponse(count=len(scenes), scenes=scenes)


class EvaluateRequest(BaseModel):
    aoi_id: str
    ndvi_mean: float = Field(ge=-1, le=1)
    threshold: float | None = Field(default=None, gt=0, le=1)


class EvaluateResponse(BaseModel):
    aoi_id: str
    should_alert: bool
    severity: str
    metric: str
    value: float
    threshold: float
    alert_id: str | None
    notified: bool


@app.post("/api/v1/alerts/evaluate", response_model=EvaluateResponse)
def evaluate_alert(req: EvaluateRequest) -> EvaluateResponse:
    """Évalue une observation NDVI, persiste l'alerte, notifie si critique.

    EN: Evaluate → persist (best-effort) → n8n webhook on critical severity.
    """
    decision = evaluate_ndvi(req.ndvi_mean, req.threshold or settings.ndvi_alert_threshold)
    alert_id: str | None = None
    notified = False

    if decision.should_alert:
        try:
            alert_id = save_alert(get_engine(), req.aoi_id, decision)
        except SQLAlchemyError as exc:
            # Best-effort : l'évaluation reste disponible sans DB / degrade gracefully
            log.warning("alert_persist_failed", aoi=req.aoi_id, error=str(exc))

        if decision.severity == "critical":
            notified = notify_n8n(
                settings.n8n_webhook_url,
                {
                    "aoi_id": req.aoi_id,
                    "alert_id": alert_id,
                    "metric": decision.metric,
                    "value": decision.value,
                    "threshold": decision.threshold,
                    "severity": decision.severity,
                },
            )

    log.info(
        "alert_evaluated",
        aoi=req.aoi_id,
        alert=decision.should_alert,
        severity=decision.severity,
        persisted=alert_id is not None,
        notified=notified,
    )
    return EvaluateResponse(
        aoi_id=req.aoi_id,
        should_alert=decision.should_alert,
        severity=decision.severity,
        metric=decision.metric,
        value=decision.value,
        threshold=decision.threshold,
        alert_id=alert_id,
        notified=notified,
    )


@app.get("/api/v1/alerts/open")
def open_alerts(
    aoi_id: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=500),
) -> dict[str, Any]:
    """Alertes non acquittées / unacknowledged alerts (503 si DB indisponible)."""
    rows = list_open_alerts(get_engine(), aoi_id, limit)
    # Sérialisation JSON des datetimes / JSON-safe serialization
    for row in rows:
        for key, val in row.items():
            if hasattr(val, "isoformat"):
                row[key] = val.isoformat()
    return {"count": len(rows), "alerts": rows}
