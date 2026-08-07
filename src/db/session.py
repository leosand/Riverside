"""Connexion base de données — engine lazy avec pooling.

EN: Lazily-created SQLAlchemy engine (cached). pool_pre_ping évite les
connexions mortes / guards against stale connections.
"""
from __future__ import annotations

from functools import lru_cache

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

from src.config import settings


@lru_cache
def get_engine() -> Engine:
    """Engine partagé / shared engine (pool de 5 connexions)."""
    return create_engine(
        settings.database_url,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=5,
    )
