"""Indices spectraux — fonctions pures, testables / pure, testable functions.

EN: NDVI/NDWI/BSI computation on xarray DataArrays. Sentinel-2 bands are
scaled by 1e4 in L2A products; values are normalized before ratio math.
"""
from __future__ import annotations

import numpy as np
import xarray as xr

S2_SCALE: float = 10_000.0  # facteur d'échelle L2A / L2A scale factor


def _norm(band: xr.DataArray) -> xr.DataArray:
    return band.astype("float32") / S2_SCALE


def compute_ndvi(red: xr.DataArray, nir: xr.DataArray) -> xr.DataArray:
    """NDVI = (NIR - Red) / (NIR + Red), borné [-1, 1]."""
    r, n = _norm(red), _norm(nir)
    denom = n + r
    ndvi = xr.where(np.abs(denom) < 1e-6, np.nan, (n - r) / denom)
    return ndvi.clip(min=-1.0, max=1.0).rename("ndvi")


def compute_ndwi(green: xr.DataArray, nir: xr.DataArray) -> xr.DataArray:
    """NDWI (McFeeters) = (Green - NIR) / (Green + NIR) — détection eau/érosion."""
    g, n = _norm(green), _norm(nir)
    denom = g + n
    ndwi = xr.where(np.abs(denom) < 1e-6, np.nan, (g - n) / denom)
    return ndwi.clip(min=-1.0, max=1.0).rename("ndwi")


def summarize(ndvi: xr.DataArray) -> dict[str, float]:
    """Statistiques agrégées pour la table ndvi_series / aggregated stats."""
    arr = ndvi.values.astype("float64")
    arr = arr[~np.isnan(arr)]
    if arr.size == 0:
        raise ValueError("NDVI vide — scène entièrement nuageuse / all-cloud scene")
    return {
        "ndvi_mean": float(arr.mean()),
        "ndvi_p10": float(np.percentile(arr, 10)),
        "ndvi_p90": float(np.percentile(arr, 90)),
    }
