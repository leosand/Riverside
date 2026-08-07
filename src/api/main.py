"""API Riverside — FastAPI, erreurs RFC 7807, logs JSON structurés.

EN: Riverside API — FastAPI with RFC 7807 problem details and structured logs.
Intégration EBP : endpoints REST versionnés /api/v1/* + webhooks (phase 2, n8n).
"""
from __future__ import annotations

from datetime import date

import structlog
from fastapi import FastAPI, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from src.alerts.thresholds import evaluate_ndvi
from src.config import settings
from src.ingest.stac_client import SceneSummary, search_scenes

log = structlog.get_logger()

app = FastAPI(
    title="Riverside API",
    version="0.1.0",
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


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError) -> JSONResponse:
    log.warning("bad_request", path=str(request.url), error=str(exc))
    return JSONResponse(
        status_code=400,
        media_type="application/problem+json",
        content=ProblemDetail(title="Bad Request", status=400, detail=str(exc)).model_dump(),
    )


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


@app.post("/api/v1/alerts/evaluate")
def evaluate_alert(req: EvaluateRequest) -> dict[str, object]:
    """Évalue une observation NDVI contre le seuil réglementaire.

    EN: Dry-run alert evaluation; persistence + n8n webhook in phase 2.
    """
    decision = evaluate_ndvi(req.ndvi_mean, req.threshold or settings.ndvi_alert_threshold)
    log.info(
        "alert_evaluated",
        aoi=req.aoi_id,
        alert=decision.should_alert,
        severity=decision.severity,
    )
    return {
        "aoi_id": req.aoi_id,
        "should_alert": decision.should_alert,
        "severity": decision.severity,
        "metric": decision.metric,
        "value": decision.value,
        "threshold": decision.threshold,
    }
