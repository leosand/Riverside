#!/usr/bin/env python3
"""Phase 4 — squelette de fine-tuning TorchGeo (segmentation berges/érosion).

EN: Fine-tuning skeleton. NON exécuté en CI (requiert GPU + dataset annoté).
Référence : torchgeo/torchgeo (~4,1k ⭐, MIT) — poids Sentinel-2 pré-entraînés
(ResNet18_Weights.SENTINEL2_ALL_MOCO) — transfer learning, pas de from-scratch.

Prérequis :
    pip install torchgeo lightning
    # Dataset d'annotation : masques raster des berges restaurées / érodées
    # (GeoTIFF alignés Sentinel-2, split SPATIAL — jamais aléatoire sur tuiles
    # adjacentes, sinon fuite spatiale / spatial leakage).

Marche à suivre documentée (audité le 2026-08) :
1. Dataset : torchgeo.datasets custom (images 13 bandes + masque binaire).
2. Sampler : RandomGeoSampler pour l'entraînement, GridGeoSampler validation.
3. Modèle : U-Net/DeepLabV3 tête segmentation + backbone pré-entraîné S2.
4. Entraînement : 1 GPU ≥ 12 Go (RTX 4060 8 Go jouable batch réduit), AMP,
   early stopping sur IoU validation spatiale.
5. Export : checkpoint → inférence tuilée sur les composites sans nuages.
"""
from __future__ import annotations


def main() -> None:
    raise SystemExit(
        "Script volontairement non exécutable : finaliser le dataset d'annotation "
        "avant le fine-tuning. Voir la docstring du module (checklist 1-5)."
    )


if __name__ == "__main__":
    main()
