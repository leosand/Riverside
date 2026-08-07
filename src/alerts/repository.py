"""Persistance des alertes — SQLAlchemy Core, portable SQLite/Postgres.

EN: Alert persistence via SQLAlchemy Core. Définition de table allégée (sans
type Geometry) pour rester testable en SQLite in-memory ; la contrainte FK et
le CHECK severity vivent dans la migration SQL (source de vérité).
"""
from __future__ import annotations

import uuid
from typing import Any

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


def save_alert(engine: Engine, aoi_id: str, decision: AlertDecision) -> str:
    """Insère une alerte en transaction / transactional insert, returns id."""
    alert_id = str(uuid.uuid4())
    with engine.begin() as conn:  # transaction auto-commit/rollback
        conn.execute(
            alerts_table.insert().values(
                id=alert_id,
                aoi_id=aoi_id,
                metric=decision.metric,
                value=decision.value,
                threshold=decision.threshold,
                severity=decision.severity,
                acknowledged=False,
            )
        )
    return alert_id


def list_open_alerts(
    engine: Engine, aoi_id: str | None = None, limit: int = 50
) -> list[dict[str, Any]]:
    """Alertes non acquittées, plus récentes d'abord / unacknowledged alerts."""
    stmt = (
        select(alerts_table)
        .where(alerts_table.c.acknowledged.is_(False))
        .order_by(alerts_table.c.raised_at.desc())
        .limit(limit)
    )
    if aoi_id is not None:
        stmt = stmt.where(alerts_table.c.aoi_id == aoi_id)
    with engine.connect() as conn:
        return [dict(row._mapping) for row in conn.execute(stmt)]
