"""Cloud removal — stratégie MVP en deux niveaux / two-tier cloud removal.

Niveau 1 (défaut, zéro entraînement) : masque SCL + composite médian temporel.
Niveau 2 (optionnel) : checkpoints pré-entraînés DSen2-CR (ameraner/dsen2-cr,
SAR-optique, SOTA sur SEN12MS-CR). Aucun GPU requis pour l'inférence ponctuelle.

EN: Tier 1 (default): SCL cloud mask + temporal median composite. Tier 2
(optional): pretrained DSen2-CR checkpoints — inference only, no training.
"""
from __future__ import annotations

import xarray as xr

# Classes SCL considérées invalides / SCL classes treated as clouds or no-data
CLOUDY_SCL: frozenset[int] = frozenset({0, 1, 3, 8, 9, 10, 11})


def scl_cloud_mask(stack: xr.DataArray) -> xr.DataArray:
    """Masque booléen des pixels valides depuis la bande SCL.

    EN: Boolean valid-pixel mask from the Scene Classification Layer.
    """
    scl = stack.sel(band="scl")
    return ~scl.isin(list(CLOUDY_SCL))


def temporal_median_composite(stack: xr.DataArray) -> xr.Dataset:
    """Composite médian sans nuages sur l'axe temporel (baseline MVP).

    Robuste, déterministe, CPU-only. EN: Cloud-free temporal median composite;
    deterministic CPU-only baseline used until DSen2-CR is wired in.
    """
    valid = scl_cloud_mask(stack)
    optical = stack.sel(band=["red", "nir"]).where(valid)
    return optical.median(dim="time", skipna=True).to_dataset(dim="band")


def run_dsen2cr_inference(scene_path: str, checkpoint_dir: str) -> None:
    """Point d'extension DSen2-CR / DSen2-CR integration hook.

    TODO(phase2): cloner https://github.com/ameraner/dsen2-cr, télécharger les
    checkpoints pré-entraînés (liens dans leur README), appeler predict().
    Risque: dépendance Keras/TF — isoler dans un conteneur dédié.
    """
    raise NotImplementedError(
        "DSen2-CR non activé au MVP — utiliser temporal_median_composite(). "
        "Voir docstring pour la marche à suivre (checkpoints pré-entraînés)."
    )
