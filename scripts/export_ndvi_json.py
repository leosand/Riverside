#!/usr/bin/env python3
"""CLI — exporte la série NDVI d'une AOI vers web/public/data/ndvi-real.json.

Usage :
    python scripts/export_ndvi_json.py --aoi-id <uuid> \
        [--out web/public/data/ndvi-real.json] [--threshold 0.30]

EN: Thin CLI wrapper around src.pipeline.export_dashboard. Requiert DATABASE_URL.
"""
from __future__ import annotations

import argparse

from src.config import settings
from src.db.session import get_engine
from src.pipeline.export_dashboard import export_ndvi_json


def main() -> None:
    parser = argparse.ArgumentParser(description="Export NDVI → dashboard JSON")
    parser.add_argument("--aoi-id", required=True, help="UUID de l'AOI")
    parser.add_argument("--out", default="web/public/data/ndvi-real.json")
    parser.add_argument("--threshold", type=float, default=settings.ndvi_alert_threshold)
    args = parser.parse_args()

    path = export_ndvi_json(get_engine(), args.aoi_id, args.out, args.threshold)
    print(f"Export écrit / written: {path}")


if __name__ == "__main__":
    main()
