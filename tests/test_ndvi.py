"""Tests unitaires indices spectraux / unit tests for spectral indices."""
import numpy as np
import pytest
import xarray as xr

from src.indices.ndvi import compute_ndvi, summarize


def _band(values: list[float]) -> xr.DataArray:
    return xr.DataArray(np.array(values, dtype="float32"))


def test_ndvi_known_values() -> None:
    # red=2000, nir=8000 (échelle 1e4) → NDVI = (0.8-0.2)/(0.8+0.2) = 0.6
    ndvi = compute_ndvi(_band([2000.0]), _band([8000.0]))
    assert float(ndvi.values[0]) == pytest.approx(0.6, abs=1e-4)


def test_ndvi_zero_denominator_is_nan() -> None:
    ndvi = compute_ndvi(_band([0.0]), _band([0.0]))
    assert np.isnan(float(ndvi.values[0]))


def test_summarize_empty_raises() -> None:
    empty = xr.DataArray(np.array([np.nan]))
    with pytest.raises(ValueError):
        summarize(empty)
