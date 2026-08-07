"""Ingestion STAC Sentinel-2 (Earth Search, données Copernicus gratuites).

EN: STAC ingestion for Sentinel-2 L2A scenes. Uses pystac-client for search and
stackstac for lazy windowed reads of cloud-optimized GeoTIFFs.
Référence repo : pystac-client, stackstac (adoptés tels quels, licences BSD/Apache).
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date

import stackstac
import xarray as xr
from pystac_client import Client
from tenacity import retry, stop_after_attempt, wait_exponential

from src.config import settings

BANDS: tuple[str, ...] = ("red", "nir", "scl")  # B04, B08, masque nuage SCL


@dataclass(frozen=True)
class SceneSummary:
    """Résumé d'une scène / Scene metadata summary."""

    item_id: str
    acquired_at: date
    cloud_cover: float


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
def search_scenes(
    bbox: tuple[float, float, float, float],
    start: date,
    end: date,
    max_cloud: float | None = None,
    limit: int = 50,
) -> list[SceneSummary]:
    """Recherche les scènes Sentinel-2 L2A les moins nuageuses sur une bbox.

    EN: Search least-cloudy Sentinel-2 L2A scenes over a bbox (WGS84).
    Raises ValueError on invalid bbox/date range.
    """
    if end < start:
        raise ValueError("end doit être >= start / end must be >= start")
    cloud = settings.max_cloud_cover if max_cloud is None else max_cloud

    catalog = Client.open(settings.stac_api_url)
    search = catalog.search(
        collections=[settings.default_collection],
        bbox=list(bbox),
        datetime=f"{start.isoformat()}/{end.isoformat()}",
        query={"eo:cloud_cover": {"lt": cloud}},
        max_items=limit,
        sortby=[{"field": "properties.eo:cloud_cover", "direction": "asc"}],
    )
    return [
        SceneSummary(
            item_id=it.id,
            acquired_at=it.datetime.date(),
            cloud_cover=float(it.properties.get("eo:cloud_cover", 100.0)),
        )
        for it in search.items()
    ]


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
def load_bands(
    item_ids: list[str],
    bbox: tuple[float, float, float, float],
    resolution: int = 10,
) -> xr.DataArray:
    """Charge les bandes red/nir/scl en lecture fenêtrée paresseuse (COG).

    EN: Lazy windowed stack of red/nir/scl bands from cloud-optimized GeoTIFFs.
    """
    if not item_ids:
        raise ValueError("item_ids ne peut être vide / must not be empty")
    catalog = Client.open(settings.stac_api_url)
    items = [catalog.get_item(i) for i in item_ids]
    return stackstac.stack(
        items,
        assets=list(BANDS),
        bounds_latlon=bbox,
        resolution=resolution,
        chunksize=2048,  # Dask chunks — maîtrise mémoire / memory control
    )
