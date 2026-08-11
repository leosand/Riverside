"""Persistance des alertes — SQLAlchemy Core, portable SQLite/Postgres.

EN: Alert persistence via SQLAlchemy Core. Définition de table allégée (sans
type Geometry) pour rester testable en SQLite in-memory ; la contrainte FK et
le CHECK severity vivent dans la migration SQL (source de vérité).
"""
from __future__ import annotations

import uuid
from typing import Any
from uuid import UUID

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    MetaData,
    String,
    Table,
    func,
    select,
    update,
)
from sqlalchemy.engine import Engine

from src.alerts.thresholds import AlertDecision

metadata = MetaData()

alerts_table = Table(
    "alerts",
    metadata,
    Column("id", String(36), primary_key=True),
    Column("aoi_id", String(36), nullable=False, index=True),
    Column("raised_at", DateTime(timezone=True), server_default=func.now()),
    Column("metric", String(64), nullable=False),
    Column("value", Float, nullable=False),
    Column("threshold", Float, nullable=False),
    Column("severity", String(16), nullable=False),
    Column("acknowledged", Boolean, nullable=False, default=False),
)

# Table aoi (référence) — JOIN pour afficher un nom lisible au lieu de l'UUID.
# EN: aoi reference table — JOIN to expose a readable name instead of the UUID.
aoi_table = Table(
    "aoi",
    metadata,
    Column("id", String(36), primary_key=True),
    Column("name", String(128), nullable=False),
)


def save_alert(engine: Engine, aoi_id: str | UUID, decision: AlertDecision) -> str:
    """Insère une alerte en transaction / transactional insert, returns id."""
    alert_id = str(uuid.uuid4())
    # Normalisation UUID → str : SQLite ne binde pas UUID natif / SQLite lacks UUID binding
    aoi_id_str = str(aoi_id)
    with engine.begin() as conn:  # transaction auto-commit/rollback
        conn.execute(
            alerts_table.insert().values(
                id=alert_id,
                aoi_id=aoi_id_str,
                metric=decision.metric,
                value=decision.value,
                threshold=decision.threshold,
                severity=decision.severity,
                acknowledged=False,
            )
        )
    return alert_id


def list_open_alerts(
    engine: Engine, aoi_id: str | UUID | None = None, limit: int = 50
) -> list[dict[str, Any]]:
    """Alertes non acquittées, plus récentes d'abord / unacknowledged alerts."""
    stmt = (
        select(alerts_table, aoi_table.c.name.label("aoi_name"))
        .select_from(
            alerts_table.outerjoin(aoi_table, alerts_table.c.aoi_id == aoi_table.c.id)
        )
        .where(alerts_table.c.acknowledged.is_(False))
        .order_by(alerts_table.c.raised_at.desc())
        .limit(limit)
    )
    if aoi_id is not None:
        stmt = stmt.where(alerts_table.c.aoi_id == str(aoi_id))
    with engine.connect() as conn:
        rows = [dict(row._mapping) for row in conn.execute(stmt)]
    # Fallback : nom inconnu → UUID tronqué (tests SQLite sans table aoi)
    for r in rows:
        if not r.get("aoi_name"):
            r["aoi_name"] = str(r["aoi_id"])[:8]
    return rows


def acknowledge_alert(engine: Engine, alert_id: str) -> bool:
    """Acquitte une alerte. False si introuvable ou déjà acquittée.

    EN: Idempotent-safe acknowledge; returns False when nothing was updated.
    """
    stmt = (
        update(alerts_table)
        .where(alerts_table.c.id == alert_id)
        .where(alerts_table.c.acknowledged.is_(False))
        .values(acknowledged=True)
    )
    with engine.begin() as conn:
        result = conn.execute(stmt)
    return result.rowcount == 1
