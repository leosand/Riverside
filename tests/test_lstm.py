"""Tests du LSTM de prévision — fenêtres glissantes et prévision autorégressive.

EN: LSTM forecast tests — sliding windows and autoregressive rollout. Les tests
sont déterministes (seed fixe) et rapides (modèles minuscules, CPU).
"""
import numpy as np
import pytest
import torch

from src.predict.vegetation_lstm import (
    ForecastResult,
    VegetationLSTM,
    forecast,
    make_windows,
)


def test_make_windows_shapes() -> None:
    """X = (n-window, window, 1) et y = (n-window, 1), alignés."""
    series = np.arange(20, dtype="float32")
    x, y = make_windows(series, window=12)
    assert tuple(x.shape) == (8, 12, 1)
    assert tuple(y.shape) == (8, 1)
    # y[i] = série[i+window] — alignement temporel
    assert float(y[0]) == float(series[12])
    assert float(y[-1]) == float(series[-1])


def test_make_windows_series_too_short() -> None:
    """Série ≤ fenêtre → ValueError explicite (pas de fenêtre vide)."""
    with pytest.raises(ValueError, match="trop courte|too short"):
        make_windows(np.array([1.0, 2.0]), window=12)
    with pytest.raises(ValueError):
        make_windows(np.arange(12, dtype="float32"), window=12)


def test_make_windows_rejects_multidim() -> None:
    with pytest.raises(ValueError):
        make_windows(np.zeros((4, 4), dtype="float32"), window=12)


def test_forecast_length_and_bounds() -> None:
    """Prédictions bornées dans [-1, 1], longueur = horizon // step."""
    torch.manual_seed(0)
    model = VegetationLSTM()
    history = np.full(24, 0.5, dtype="float32")
    res = forecast(model, history, horizon_days=30, step_days=5)
    assert isinstance(res, ForecastResult)
    assert len(res.predicted_ndvi) == 6
    assert all(-1.0 <= p <= 1.0 for p in res.predicted_ndvi)


def test_forecast_detects_breach() -> None:
    """Série basse → premier jour de franchissement du seuil détecté."""
    torch.manual_seed(0)
    model = VegetationLSTM()
    history = np.full(24, 0.10, dtype="float32")
    res = forecast(model, history, horizon_days=30, step_days=5, threshold=0.30)
    assert res.below_threshold_at is not None
    assert res.below_threshold_at == 5  # 1er pas = jour 5


def test_forecast_no_breach_when_threshold_low() -> None:
    """Seuil très bas → aucune brèche détectée sur l'horizon."""
    torch.manual_seed(0)
    model = VegetationLSTM()
    history = np.full(24, 0.9, dtype="float32")
    res = forecast(model, history, horizon_days=15, step_days=5, threshold=-1.0)
    assert res.below_threshold_at is None
