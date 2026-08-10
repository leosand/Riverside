# Vérification & Validation (V&V) — Riverside v0.3.0

## Méthodologie

- **Vérification** : le système est-il construit correctement ? (tests unitaires,
  intégration, E2E, lint, schéma, compilation TypeScript, tests navigateur)
- **Validation** : construit-on le bon système ? (exactitude numérique des indices,
  comportement métier des alertes, parcours utilisateur complet)

## Matrice de traçabilité exigences → tests (statut RÉEL mesuré)

Campagne d'exécution : 2026-08-07 — Python 3.12.10, pytest 9.1.1, ruff 0.16.1,
TypeScript 5.5.3 / Next.js 14, Playwright 1.62.1.
Résultats réels : **34 tests pytest passés / 0 échoué**, **3 tests Playwright
frontend passés / 0 échoué**, **1 test STAC live passant** (réseau réel, hors
CI), **5 erreurs de lint corrigées** (état final : 0), **0 échec initial** sur
les 22 tests d'origine.

| Exigence | Vérifiée par | Statut RÉEL |
|---|---|---|
| NDVI = (NIR−R)/(NIR+R), borné [−1,1] | `tests/test_ndvi.py::test_ndvi_known_values` (valeur connue 0.6) | ✅ PASS |
| Division par zéro → NaN | `test_ndvi_zero_denominator_is_nan` | ✅ PASS |
| Scène 100 % nuageuse → erreur explicite | `test_summarize_empty_raises`, E2E `test_e2e_all_cloud_scene_raises` | ✅ PASS |
| Seuil réglementaire → alerte warning/critical | `tests/test_alerts.py` (3 cas de bord) | ✅ PASS |
| Persistance transactionnelle des alertes | `tests/test_repository.py` | ✅ PASS |
| Pas de dérive schéma vs migration SQL | `test_table_matches_migration_columns` | ✅ PASS |
| Acquittement idempotent-safe | `tests/test_acknowledge.py` (inconnu, double) | ✅ PASS |
| Webhook n8n best-effort, jamais bloquant | `tests/test_notify.py` | ✅ PASS |
| API dégradée gracieusement sans DB | `test_evaluate_alert_critical_without_db_still_200` | ✅ PASS |
| Erreurs RFC 7807 (400/404/503) | `tests/test_api.py`, E2E `test_e2e_alert_lifecycle` | ✅ PASS |
| Chaîne complète scène→composite→NDVI→série→alerte | `tests/e2e/test_pipeline_e2e.py` (scène synthétique) | ✅ PASS |
| Cycle API complet evaluate→open→ack→open vide | `tests/e2e/test_api_e2e.py` | ✅ PASS |
| Compilation frontend TypeScript strict, zéro `any` | `npx tsc --noEmit` dans `web/` | ✅ PASS |
| Lint Python (ruff) | `ruff check src tests` | ✅ PASS (après 5 corrections) |
| Job d'ingestion (nominal, `no_scenes`, `all_cloud`) | `tests/test_ingest_job.py` (mocks monkeypatch) | ✅ PASS |
| LSTM : fenêtres glissantes + prévision bornée | `tests/test_lstm.py` (forme, bornes [-1,1], brèche) | ✅ PASS |
| Contrat STAC (réponse Earth Search mockée) | `tests/test_stac_contract.py` (`responses`) | ✅ PASS |
| Parcours frontend complet (SSR, erreur API, carte) | `web/e2e/dashboard.spec.ts` (Playwright chromium) | ✅ PASS |
| Intégration STAC réelle (Earth Search) | `tests/test_stac_live.py` (marker `integration`, hors CI) | ✅ PASS (réseau OK) |

**Totaux mesurés** : 34 tests pytest · 3 tests Playwright · 1 test STAC live ·
0 échoué · 5 erreurs de lint corrigées · 1 erreur de dépendance npm corrigée
· 12 tests pytest ajoutés en durcissement · 3 tests frontend ajoutés.

## Journal des corrections (campagne initiale)

| Fichier | Problème | Cause racine | Correction appliquée | Test de non-régression |
|---|---|---|---|---|
| `tests/e2e/test_pipeline_e2e.py` | ruff F401 : import `ndvi_series_table` inutilisé | Import orphelin laissé lors de l'écriture du test | Suppression de l'import + tri du bloc (ruff `--fix`, I001) | E2E pipeline : 2 PASSED |
| `tests/e2e/test_pipeline_e2e.py` | ruff C408 : `dict()` inutile | Style | Réécriture en littéral `{"band": "scl"}` (mutation `.loc` inchangée — la bande SCL est bien mutée, vérifié : test passe) | `test_e2e_all_cloud_scene_raises` PASSED |
| `src/api/main.py` | ruff B008 ×2 : `Query()` appelé en valeur par défaut | Style FastAPI moderne | Passage au style `Annotated[...]` (contraintes `ge/le` conservées) | `tests/test_api.py` : 4 PASSED |
| `web/package.json` | `npm install` échoue : ETARGET `@types/maplibre-gl@^4.0.0` | Le package n'existe pas sur npm (max 1.14.0) ; maplibre-gl v4 embarque ses types | Suppression du devDependency invalide | `npx tsc --noEmit` : 0 erreur |
| `web/package.json` | TypeScript : TS2688 type `react-dom` introuvable | `@types/react-dom` absent des devDependencies (requis par Next 14) | Ajout de `@types/react-dom@^18.3.0` | `npx tsc --noEmit` : 0 erreur |

## Journal des ajouts (actions post-campagne)

| Fichier | Action | Résultat |
|---|---|---|
| `requirements-dev.txt` | Séparation des dépendances de test (ruff, pytest, responses) hors prod | Install CI : `pip install -r requirements.txt -r requirements-dev.txt` |
| `web/playwright.config.ts` + `web/e2e/dashboard.spec.ts` | Tests navigateur frontend (port 3101 dédié, `reuseExistingServer: false`) | 3 PASSED — titre, erreur API (role=alert filtré), carte MapLibre |
| `tests/test_stac_live.py` + `pytest.ini` | Test d'intégration STAC réel, marker `integration` exclu par défaut | PASSED en local (Earth Search, 3.3s) ; hors CI |
| `.github/workflows/ci.yml` | Ajout de l'étape Playwright (`--with-deps chromium`) | CI verte sur le commit précédent |

**Note Playwright** : le port 3100 était occupé par un autre projet
(Towncenter-DMV) sur la machine de dev — la config utilise 3101 et force
`reuseExistingServer: false` pour garantir que le serveur Next.js du repo est
testé, jamais un serveur étranger.

## Validation numérique (E2E synthétique) — confirmée

La scène synthétique (red=2000, nir=8000, échelle 1e4) produit un NDVI attendu
de **0.6** ; le test E2E vérifie et **confirme** :
1. Le composite médian exclut bien les pixels SCL=8 (nuages) de la date t1.
2. `ndvi_mean ≈ 0.6` (tolérance 1e-4) — exactitude de bout en bout. ✅ mesuré
   `pytest.approx(0.6, abs=1e-4)` passe.
3. `p10 ≤ mean ≤ p90` — cohérence des quantiles. ✅
4. NDVI 0.20 vs seuil 0.30 → sévérité `critical` → persistance → acquittement. ✅

Le masque SCL exclut les pixels nuageux : le scénario tout-nuageux lève
`ValueError("... nuageuse / all-cloud scene")` — le `pytest.raises(match="nuageuse|cloud")`
correspond au message réel de `src/indices/ndvi.py::summarize`.

## Exécution

```bash
pip install -r requirements.txt -r requirements-dev.txt  # deps + dev
pytest tests/ -v          # offline par défaut (34 tests) — marker integration exclu
ruff check src tests      # lint (CI) — 0 erreur
cd web && npm ci && npx tsc --noEmit   # TypeScript strict — 0 erreur
cd web && npx playwright test          # E2E frontend — 3 tests (démarre Next.js :3101)
pytest tests/test_stac_live.py -m integration -v  # STAC réel (réseau, hors CI)
```

La CI GitHub Actions (`.github/workflows/ci.yml`) rejoue lint + tests +
typecheck + Playwright à chaque push/PR sur Python 3.12. Statut CI réel :
**success** sur les commits `730d630` (campagne V&V), `c7abe93` (actions 1-3)
et `b6aeebd` (fix aoi_id UUID + déploiement Docker).

## Déploiement Docker (validation environnement réelle)

| Élément | Valeur mesurée |
|---|---|
| Docker / Compose | 29.6.2 / v5.3.1 |
| Stack | `db` (postgis/postgis:16-3.4) + `api` (Dockerfile non-root) + `n8n` |
| Ports dédiés (override) | API `:8001`, PostGIS `:5433`, n8n `:5679` — nécessaires car `5432/3000/8000` occupés par d'autres projets locaux (towncenter, uvicorn) |
| `docker compose config` | ✅ valide (warning `version` obsolète retiré) |
| `/health` | `{"status":"ok","service":"riverside"}` (mesuré) |
| `/docs` (OpenAPI) | Swagger UI accessible (mesuré) |
| `db` PostGIS (migration 001) | ✅ healthy — tables `aoi`, `scenes`, `ndvi_series`, `alerts` créées (mesuré) |
| n8n | ✅ HTTP 200 sur `http://localhost:5679` (mesuré) |

Déploiement :

```bash
cp .env.example .env          # ajustez DATABASE_URL / secrets
docker compose -f docker-compose.yml -f docker-compose.override.yml up -d --build
curl http://localhost:8001/health          # API
cd web && NEXT_PUBLIC_API_URL=http://localhost:8001 npm run build
cd web && NEXT_PUBLIC_API_URL=http://localhost:8001 npx next start -p 3101   # frontend
```

**URLs du dashboard** :
- Frontend (dashboard visuel) : http://localhost:3101
- API (OpenAPI) : http://localhost:8001/docs
- n8n : http://localhost:5679

> NB : l'URL racine de l'API (`:8001/`) renvoie `{"detail":"Not Found"}` — c'est
> le comportement normal de FastAPI (pas de route `/`). Le dashboard visuel est
> servi par le frontend Next.js sur `:3101`, qui appelle l'API sur `:8001`.

**Corrections apportées au cours du déploiement réel** :
- `Dockerfile` : `pip install` avec `--retries 5 --timeout 300` — le build
  échouait sur un `Read timed out` de pip (réseau lent, torch 526 MB).
- `Dockerfile` : ajout de `libexpat1` (lib système) — le conteneur API
  échouait au démarrage avec `ImportError: libexpat.so.1` (requis par
  rasterio/stackstac sur les images `python:slim`).
- `docker-compose.yml` : les `ports:` par défaut (5432/3000/8000) ont été
  retirés du fichier de base — Compose v2 **fusionne** les listes `ports` au
  lieu de les remplacer, ce qui laissait les ports par défaut actifs en plus
  des ports dédiés de l'override (conflit avec towncenter). Les ports vivent
  désormais uniquement dans `docker-compose.override.yml`.

**État mesuré du déploiement** :
- ✅ `db` PostGIS : healthy sur `:5433`, migration 001 appliquée (tables
  `aoi`, `scenes`, `ndvi_series`, `alerts` vérifiées).
- ✅ `n8n` : HTTP 200 sur `http://localhost:5679`.
- ✅ API FastAPI : `/health` 200, RFC 7807 (400), et **cycle complet
  evaluate→open→acknowledge→open vide validé contre le Postgres Docker**
  sur `http://localhost:8001` (conteneur Docker `riverside-api` (image avec libexpat, ports dédiés).
  Le build a été relancé 4 fois (réseau local instable, ~80 kB/s vers PyPI)
  avant d'aboutir — le retry pip (`--retries 5 --timeout 300`) a fini par passer).
- 🐛 **Désalignement contrat API ↔ schéma Postgres découvert et CORRIGÉ** : la
  migration 001 définit `alerts.aoi_id`/`ndvi_series.aoi_id`/`scenes.aoi_id`
  comme `UUID NOT NULL`, mais l'API acceptait un `aoi_id` texte libre
  (`"demo-docker"`). En SQLite (tests) tout passait ; en Postgres réel →
  `InvalidTextRepresentation` (UUID), masqué en 503 par la persistance
  best-effort. **Correction appliquée (validée par l'utilisateur, UUID strict)** :
  - `src/api/main.py` : `aoi_id: UUID` dans `EvaluateRequest`/`EvaluateResponse`
    et le query param `open_alerts`.
  - `src/pipeline/ingest_job.py` : `aoi_id: UUID` dans `run_ingestion`.
  - `src/alerts/repository.py` + `src/pipeline/repository.py` : normalisation
    `str(aoi_id)` avant persistance (SQLite ne binde pas UUID natif).
  - Tests mis à jour avec des UUID fixes lisibles (`aaaaaaaa-...`, etc.).
  - **Validé en conditions réelles** : cycle complet evaluate→open→ack→open vide
    sur le Postgres Docker (:5433), après insertion de l'AOI de référence
    (FK `alerts_aoi_id_fkey` vérifiée — l'alerte exige une AOI existante).

## Couverture fonctionnelle

| Exigence | État | Plan |
|---|---|---|
| Appels STAC réels (Earth Search) | ✅ Couverte (contractuel + live marqué) | `test_stac_live.py` en CI optionnelle si réseau autorisé |
| Frontend Playwright (parcours UI) | ✅ Couverte — `web/e2e/dashboard.spec.ts` | Étendre : acquittement via l'UI avec un backend mocké |
| Job d'ingestion avec mocks réseau | ✅ Couverte — `tests/test_ingest_job.py` | Étendre au scénario avec alerte critique persistée |
| Prédiction LSTM | ✅ Couverte — `tests/test_lstm.py` | Entraînement réel sur série NDVI historique (phase 5) |

## Limites connues / Known limitations

- `test_open_alerts_db_unavailable_returns_503_rfc7807` est un test
  **d'environnement** : il valide la dégradation 503 quand aucune DB n'est
  joignable. Avec le Postgres Docker actif, il passe naturellement au vert
  (l'API répond 200). Vérifié : 1 passed DB arrêtée.
- Le test STAC live dépend du réseau : exclu de la suite par défaut
  (marker `integration`) pour garder la CI déterministe.
- Playwright lance un build Next.js de production à chaque exécution (~30-40 s)
  — acceptable en CI, plus lent en local.
- La migration 001 utilise `gen_random_uuid()` : exécuter `CREATE EXTENSION pgcrypto`
  si erreur sur Postgres < 13.
- `docker-compose.yml` et `.env.example` contiennent un mot de passe de
  démonstration (`changeme`) — à remplacer par un secret store en production
  (TODO documenté).
- Warning pytest non bloquant : `StarletteDeprecationWarning` (TestClient httpx)
  — à résoudre lors d'une montée de version FastAPI/Starlette.
