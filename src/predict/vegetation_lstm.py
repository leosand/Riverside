"""Modèle prédictif de croissance végétale — LSTM léger, CPU-friendly.

EN: Lightweight LSTM forecasting NDVI trajectories. Deliberately small
(hidden=32) so training runs on CPU in minutes; no GPU required at MVP.
Pas de modèles de diffusion au MVP — surdimensionné / no diffusion models.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import torch
from torch import nn


@dataclass(frozen=True)
class ForecastResult:
    horizon_days: int
    predicted_ndvi: list[float]
    below_threshold_at: int | None  # jour du 1er passage sous seuil / first breach day


class VegetationLSTM(nn.Module):
    """LSTM 1 couche → tête linéaire / single-layer LSTM with linear head."""

    def __init__(self, hidden_size: int = 32) -> None:
        super().__init__()
        self.lstm = nn.LSTM(input_size=1, hidden_size=hidden_size, batch_first=True)
        self.head = nn.Linear(hidden_size, 1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        out, _ = self.lstm(x)
        return self.head(out[:, -1, :])


def make_windows(series: np.ndarray, window: int) -> tuple[torch.Tensor, torch.Tensor]:
    """Fenêtres glissantes (X, y) / sliding-window supervised pairs."""
    if series.ndim != 1 or series.size <= window:
        raise ValueError("Série trop courte pour la fenêtre demandée / series too short")
    xs = np.stack([series[i : i + window] for i in range(series.size - window)])
    ys = series[window:]
    return (
        torch.tensor(xs, dtype=torch.float32).unsqueeze(-1),
        torch.tensor(ys, dtype=torch.float32).unsqueeze(-1),
    )


def train(series: np.ndarray, window: int = 12, epochs: int = 200, lr: float = 1e-3) -> VegetationLSTM:
    """Entraînement CPU / CPU training (minutes, not hours)."""
    torch.manual_seed(42)  # reproductibilité / reproducibility
    model = VegetationLSTM()
    opt = torch.optim.Adam(model.parameters(), lr=lr)
    loss_fn = nn.MSELoss()
    x, y = make_windows(series, window)
    model.train()
    for _ in range(epochs):
        opt.zero_grad()
        loss = loss_fn(model(x), y)
        loss.backward()
        opt.step()
    return model


def forecast(
    model: VegetationLSTM,
    history: np.ndarray,
    horizon_days: int,
    step_days: int = 5,
    threshold: float = 0.30,
) -> ForecastResult:
    """Prévision autorégressive + détection de franchissement de seuil.

    EN: Autoregressive rollout; reports first day NDVI drops below threshold.
    """
    model.eval()
    hist = history.astype("float32").tolist()
    preds: list[float] = []
    breach: int | None = None
    with torch.no_grad():
        for k in range(horizon_days // step_days):
            window = torch.tensor(hist[-12:], dtype=torch.float32).view(1, -1, 1)
            nxt = float(model(window).item())
            nxt = max(-1.0, min(1.0, nxt))
            preds.append(nxt)
            hist.append(nxt)
            if breach is None and nxt < threshold:
                breach = (k + 1) * step_days
    return ForecastResult(horizon_days, preds, breach)
