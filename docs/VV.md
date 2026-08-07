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
**success** sur le commit `730d630` (campagne V&V).

## Couverture fonctionnelle

| Exigence | État | Plan |
|---|---|---|
| Appels STAC réels (Earth Search) | ✅ Couverte (contractuel + live marqué) | `test_stac_live.py` en CI optionnelle si réseau autorisé |
| Frontend Playwright (parcours UI) | ✅ Couverte — `web/e2e/dashboard.spec.ts` | Étendre : acquittement via l'UI avec un backend mocké |
| Job d'ingestion avec mocks réseau | ✅ Couverte — `tests/test_ingest_job.py` | Étendre au scénario avec alerte critique persistée |
| Prédiction LSTM | ✅ Couverte — `tests/test_lstm.py` | Entraînement réel sur série NDVI historique (phase 5) |

## Limites connues / Known limitations

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
