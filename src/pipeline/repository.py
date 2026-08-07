"""Persistance des séries NDVI — SQLAlchemy Core, portable SQLite/Postgres.

EN: NDVI time-series persistence. Migration 001_init.sql reste la source de
vérité (PK composite aoi_id+observed_at, FK vers aoi).
"""
from __future__ import annotations

from datetime import date
from uuid import UUID

from sqlalchemy import Column, Date, Float, MetaData, String, Table
from sqlalchemy.engine import Engine

metadata = MetaData()

ndvi_series_table = Table(
    "ndvi_series",
    metadata,
    Column("aoi_id", String(36), primary_key=True),
    Column("observed_at", Date, primary_key=True),
    Column("ndvi_mean", Float, nullable=False),
    Column("ndvi_p10", Float),
    Column("ndvi_p90", Float),
    Column("ndwi_mean", Float),
)


def save_ndvi_series(
    engine: Engine,
    aoi_id: str | UUID,
    observed_at: date,
    stats: dict[str, float],
    ndwi_mean: float | None = None,
) -> None:
    """Upsert d'un point de série / upsert one series point (delete+insert)."""
    # Normalisation UUID → str : SQLite ne binde pas UUID natif / SQLite lacks UUID binding
    aoi_id_str = str(aoi_id)
    with engine.begin() as conn:
        conn.execute(
            ndvi_series_table.delete().where(
                ndvi_series_table.c.aoi_id == aoi_id_str,
                ndvi_series_table.c.observed_at == observed_at,
            )
        )
        conn.execute(
            ndvi_series_table.insert().values(
                aoi_id=aoi_id_str,
                observed_at=observed_at,
                ndvi_mean=stats["ndvi_mean"],
                ndvi_p10=stats.get("ndvi_p10"),
                ndvi_p90=stats.get("ndvi_p90"),
                ndwi_mean=ndwi_mean,
            )
        )
