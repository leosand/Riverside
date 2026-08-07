# Riverside

> Surveillance automatisée des berges — imagerie satellite + IA, 100 % open source.
> Automated shoreline monitoring — satellite imagery + AI, fully open source.

![CI](https://github.com/leosand/Riverside/actions/workflows/ci.yml/badge.svg)
![Tests](https://img.shields.io/badge/tests-34%20passed%20%7C%200%20failed-brightgreen)

## Contexte / Context

Inspiré du concept **RiverRise** (ThinkBotics, Team 29) : les inspections manuelles des berges du bassin des Grands Lacs sont coûteuses et peu fréquentes. Riverside automatise le suivi de la couverture végétale (NDVI) à partir d'images Sentinel-2 gratuites, détecte les zones sous-restaurées et érodables, prédit la croissance de la végétation et notifie tout dépassement de seuil réglementaire CSR.

## Architecture

```
Sentinel-2 L2A (Earth Search STAC, gratuit)
   │  src/ingest/stac_client.py  (pystac-client + stackstac)
   ▼
Cloud removal — src/cloud_removal/run_dsen2cr.py
   │  MVP : masque SCL + composite médian temporel
   │  Option : checkpoints pré-entraînés DSen2-CR
   ▼
Indices NDVI/NDWI — src/indices/ndvi.py
   ▼
Job d'ingestion — src/pipeline/ingest_job.py (série + alertes + n8n)
   ▼
Prédiction LSTM — src/predict/vegetation_lstm.py (CPU)
   ▼
API FastAPI v0.3 — src/api/main.py (RFC 7807)
   ▼
Frontend Next.js + MapLibre — web/ (SSR, SEO/AEO, a11y)
```

Docs : [Architecture](docs/ARCHITECTURE.md) · [V&V](docs/VV.md) · OpenAPI : `/docs` sur l'API.

## GitHub Reference Audit (choix d'adoption)

| Repo | Rôle | Verdict |
|---|---|---|
| torchgeo/torchgeo (4,1k ⭐, MIT) | Segmentation berges, poids Sentinel-2 | Adopter (phase 4) |
| ameraner/dsen2-cr (180 ⭐) | Cloud removal SAR-optique, checkpoints fournis | Adopter en option |
| Penn000/SpA-GAN_for_cloud_removal | Baseline recherche | Inspiration seulement |
| pystac-client / stackstac / rioxarray | Ingestion + raster | Adoptés tels quels |

## Démarrage rapide / Quickstart

```bash
cp .env.example .env
docker compose up -d db n8n
pip install -r requirements.txt
pip install responses        # dev — test contractuel STAC
psql $DATABASE_URL -f db/migrations/001_init.sql
uvicorn src.api.main:app --reload   # API : http://localhost:8000/docs
cd web && npm install && npm run dev  # Frontend : http://localhost:3000
pytest tests/ -v                      # 34 tests, tout offline
```

**Statut des tests (2026-08-07)** : 34/34 passés, 0 échec — `ruff` 0 erreur,
`tsc --noEmit` 0 erreur. Détails dans [docs/VV.md](docs/VV.md).

## API (v0.3)

| Méthode | Endpoint | Rôle |
|---|---|---|
| GET | `/health` | Santé du service |
| GET | `/api/v1/scenes` | Recherche scènes Sentinel-2 (bbox, dates) |
| POST | `/api/v1/alerts/evaluate` | Évalue NDVI vs seuil → persiste + notifie si critique |
| GET | `/api/v1/alerts/open` | Alertes non acquittées |
| POST | `/api/v1/alerts/{id}/acknowledge` | Acquitte une alerte (404 sinon) |

## Sécurité & conformité

- Aucun secret codé en dur — variables d'environnement uniquement (.env, jamais commité).
- Données Copernicus libres de droits ; traitement local possible (Loi 25 friendly).
- API : CORS restreint, erreurs RFC 7807, logs JSON structurés (structlog).
- CI : ruff + pytest à chaque push (GitHub Actions).

## Roadmap

- [x] Phase 1 — MVP : NDVI + alertes + tests
- [x] Phase 2 — CI, persistance SQLAlchemy, webhook n8n
- [x] Phase 3 — Acknowledge, job ingestion, frontend MapLibre, E2E + V&V
- [x] Phase 3.5 — V&V approfondie : durcissement tests (ingest_job, LSTM, STAC contractuel), lint + tsc à 0
- [ ] Phase 4 — Playwright frontend, fine-tuning TorchGeo, DSen2-CR en production
- [ ] Phase 5 — Rapports CSR bilingues FR/EN via LLM local (Ollama), intégration EBP
