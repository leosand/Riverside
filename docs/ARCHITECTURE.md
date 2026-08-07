# Architecture — Riverside

## Vue d'ensemble / Overview

Riverside est un pipeline de surveillance des berges en trois couches :

1. **Acquisition** — `src/ingest/stac_client.py` interroge l'API STAC Earth Search
   (Sentinel-2 L2A, gratuit) et charge les bandes red/nir/scl en lecture fenêtrée
   paresseuse (stackstac + Dask, COG).
2. **Traitement IA** — cloud removal (`src/cloud_removal/`, composite médian SCL
   au MVP, DSen2-CR pré-entraîné en option), indices spectraux (`src/indices/`),
   prédiction LSTM (`src/predict/`).
3. **Décision & exposition** — règles de seuils (`src/alerts/thresholds.py`),
   persistance PostGIS (`src/alerts/repository.py`, `src/pipeline/repository.py`),
   notification n8n (`src/alerts/notify.py`), API FastAPI (`src/api/main.py`),
   frontend Next.js + MapLibre (`web/`).

## Flux de données du job d'ingestion

```
cron/n8n → run_ingestion(engine, aoi_id, bbox, start, end)
  ├─ search_scenes()          → scènes triées par couverture nuageuse
  ├─ load_bands()             → stack xarray (time, band, y, x)
  ├─ temporal_median_composite() → image sans nuages
  ├─ compute_ndvi() + summarize() → stats agrégées
  ├─ save_ndvi_series()       → upsert en base (transaction)
  └─ evaluate_ndvi()          → save_alert() + notify_n8n() si critique
```

Le rapport `IngestionReport` capture les erreurs sans lever d'exception —
un lot (batch) continue même si une AOI échoue.

## Décisions d'architecture (ADR résumé)

| # | Décision | Alternatives rejetées | Justification |
|---|---|---|---|
| 1 | Composite médian SCL au MVP | SpA-GAN, diffusion | Zéro entraînement, déterministe, CPU-only ; DSen2-CR documenté en phase 2 |
| 2 | SQLAlchemy Core (pas ORM) | Django ORM, Prisma | Testable SQLite in-memory, schéma SQL = source de vérité |
| 3 | Persistance best-effort dans l'API | Échec 503 sur evaluate | La décision d'alerte ne doit jamais dépendre de la DB |
| 4 | n8n webhook fire-and-log | File Kafka, Celery | MVP : retry ×3 suffit ; pas d'infra de file à maintenir |
| 5 | LSTM 32 unités | VAE/diffusion (pitch) | Séries 1D courtes ; entraînement CPU en minutes |
| 6 | Next.js SSR + MapLibre | SPA client-only, Google Maps | SEO/AEO, SSR, fond OSM libre (100 % open source) |

## Five Pillars (frontend `web/`)

- **SEO** : metadata dynamiques, `lang="fr-CA"`, Open Graph, SSR (`force-dynamic`),
  HTML sémantique (h1, section, aria-labelledby).
- **AEO/GEO** : JSON-LD `WebApplication`, contenu factuel structuré.
- **SXO** : skip link, carte accessible clavier, états d'erreur explicites (`role="alert"`).
- **Sécurité** : en-têtes OWASP dans `next.config.mjs`, `robots: noindex` (outil interne).

## Sécurité & conformité

- Secrets en variables d'environnement uniquement (`.env` jamais commité, `.gitignore`).
- API : CORS restreint, erreurs RFC 7807, pas de stack trace exposée.
- Conteneur API non-root (Dockerfile), healthchecks dans docker-compose.
- Données Copernicus libres ; traitement local compatible Loi 25.
