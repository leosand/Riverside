"""Export des séries NDVI vers le JSON consommé par le dashboard Next.js.

EN: Export ndvi_series → web/public/data/ndvi-real.json. Requête SQL directe
(sqlalchemy.text) pour ne PAS dépendre de l'évolution de repository.py —
résilient aux renommages internes / resilient to internal refactors.

Schéma produit (source de vérité côté export ; adapter NdviSeriesChart.tsx ici
si le contrat change) :
{
  "meta":     {"source": "pipeline", "generated_at": ISO, "aoi_id": str},
  "aoi":      {"id": str, "bbox": [minx, miny, maxx, maxy] | null},
  "threshold": float,
  "series":   [{"date": "YYYY-MM-DD", "ndvi_mean": float,
                "ndvi_p10": float|null, "ndvi_p90": float|null,
                "ndwi_mean": float|null}, ...]  # trié par date croissante
}
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy import text
from sqlalchemy.engine import Engine

_QUERY = text(
    """
    SELECT observed_at, ndvi_mean, ndvi_p10, ndvi_p90, ndwi_mean
    FROM ndvi_series
    WHERE aoi_id = :aoi_id
    ORDER BY observed_at ASC
    """
)


def build_dashboard_payload(
    engine: Engine,
    aoi_id: str,
    threshold: float,
    bbox: list[float] | None = None,
) -> dict[str, Any]:
    """Construit la charge utile JSON du dashboard / build dashboard payload.

    Raises ValueError si la série est vide (rien à afficher).
    """
    with engine.connect() as conn:
        rows = conn.execute(_QUERY, {"aoi_id": aoi_id}).mappings().all()
    if not rows:
        raise ValueError(f"Aucune série NDVI pour aoi_id={aoi_id} / empty series")

    series = [
        {
            "date": row["observed_at"].isoformat()
            if hasattr(row["observed_at"], "isoformat")
            else str(row["observed_at"]),
            "ndvi_mean": float(row["ndvi_mean"]),
            "ndvi_p10": None if row["ndvi_p10"] is None else float(row["ndvi_p10"]),
            "ndvi_p90": None if row["ndvi_p90"] is None else float(row["ndvi_p90"]),
            "ndwi_mean": None if row["ndwi_mean"] is None else float(row["ndwi_mean"]),
        }
        for row in rows
    ]
    return {
        "meta": {
            "source": "pipeline",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "aoi_id": aoi_id,
        },
        "aoi": {"id": aoi_id, "bbox": bbox},
        "threshold": threshold,
        "series": series,
    }


def export_ndvi_json(
    engine: Engine,
    aoi_id: str,
    out_path: str | Path,
    threshold: float = 0.30,
    bbox: list[float] | None = None,
) -> Path:
    """Écrit le JSON du dashboard (crée les dossiers parents) / write JSON file."""
    payload = build_dashboard_payload(engine, aoi_id, threshold, bbox)
    path = Path(out_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return path
