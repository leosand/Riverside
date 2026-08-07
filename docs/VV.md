# Vérification & Validation (V&V) — Riverside v0.3.0

## Méthodologie

- **Vérification** : le système est-il construit correctement ? (tests unitaires,
  intégration, E2E, lint, schéma, compilation TypeScript)
- **Validation** : construit-on le bon système ? (exactitude numérique des indices,
  comportement métier des alertes, parcours utilisateur complet)

## Matrice de traçabilité exigences → tests (statut RÉEL mesuré)

Campagne d'exécution : 2026-08-07 — Python 3.12.10, pytest 9.1.1, ruff 0.16.1,
TypeScript 5.5.3 / Next.js 14. Résultats réels : **34 tests exécutés, 34 passés,
0 échoué** (dont 12 tests ajoutés en durcissement, étape 4), **5 erreurs de
lint corrigées** (état final : 0), **0 échec initial** sur les 22 tests d'origine.

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

**Totaux mesurés** : 34 tests exécutés · 34 passés · 0 échoué · 0 corrigé
(logique) · 5 erreurs de lint corrigées · 1 erreur de dépendance npm corrigée
· 12 tests ajoutés en durcissement (étape 4).

## Journal des corrections

| Fichier | Problème | Cause racine | Correction appliquée | Test de non-régression |
|---|---|---|---|---|
| `tests/e2e/test_pipeline_e2e.py` | ruff F401 : import `ndvi_series_table` inutilisé | Import orphelin laissé lors de l'écriture du test | Suppression de l'import + tri du bloc (ruff `--fix`, I001) | E2E pipeline : 2 PASSED |
| `tests/e2e/test_pipeline_e2e.py` | ruff C408 : `dict()` inutile | Style | Réécriture en littéral `{"band": "scl"}` (mutation `.loc` inchangée — la bande SCL est bien mutée, vérifié : test passe) | `test_e2e_all_cloud_scene_raises` PASSED |
| `src/api/main.py` | ruff B008 ×2 : `Query()` appelé en valeur par défaut | Style FastAPI moderne | Passage au style `Annotated[...]` (contraintes `ge/le` conservées) | `tests/test_api.py` : 4 PASSED |
| `web/package.json` | `npm install` échoue : ETARGET `@types/maplibre-gl@^4.0.0` | Le package n'existe pas sur npm (max 1.14.0) ; maplibre-gl v4 embarque ses types | Suppression du devDependency invalide | `npx tsc --noEmit` : 0 erreur |
| `web/package.json` | TypeScript : TS2688 type `react-dom` introuvable | `@types/react-dom` absent des devDependencies (requis par Next 14) | Ajout de `@types/react-dom@^18.3.0` | `npx tsc --noEmit` : 0 erreur |

Aucun test n'a été supprimé, désactivé (`pytest.skip`) ou affaibli. Les corrections
sont minimales et ciblées ; aucune logique métier n'a été modifiée.

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
pytest tests/ -v          # unitaires + intégration + E2E + durcissement (tout offline) — 34 passés
ruff check src tests      # lint (CI) — 0 erreur
cd web && npx tsc --noEmit # TypeScript strict — 0 erreur
```

Le test contractuel STAC utilise `responses` (dépendance de test) :

```bash
pip install responses   # dev — requise pour tests/test_stac_contract.py
```

La CI GitHub Actions (`.github/workflows/ci.yml`) rejoue lint + tests à chaque
push/PR sur Python 3.12. Il est recommandé d'y ajouter l'installation de
`responses` (dev) et l'étape `npx tsc --noEmit` (frontend).

## Couverture fonctionnelle restante (phase 4)

Exigences **NON couvertes** par la campagne actuelle :

| Exigence | État | Plan phase 4 |
|---|---|---|
| Appels STAC réels (Earth Search) | ✅ Couverte (contractuel) — `tests/test_stac_contract.py` : réponse Earth Search minimale mockée (`responses`), parsing + requête vérifiés | Remplacer le mock par un vrai endpoint STAC (intégration réseau, hors CI) |
| Frontend Playwright (parcours UI complet) | Non couverte | `web/e2e/*.spec.ts` Playwright : chargement, erreur API, acquittement via l'UI |
| Job d'ingestion avec mocks réseau | ✅ Couverte — `tests/test_ingest_job.py` : `run_ingestion` avec `search_scenes`/`load_bands` monkeypatchés (nominal, `no_scenes`, `all_cloud`) | Étendre au scénario avec alerte critique persistée |
| Prédiction LSTM (fenêtres, prévision) | ✅ Couverte — `tests/test_lstm.py` : `make_windows` (forme, série courte, multidim), `forecast` (longueur, bornes [-1,1], brèche, pas de brèche) | Entraînement réel sur série NDVI historique (phase 5) |

## Limites connues / Known limitations

- Les appels STAC réels (réseau) ne sont pas couverts par les tests — à mocker
  avec `responses`/`respx` en phase 4 (test d'intégration contractuelle).
- Le frontend n'a pas encore de tests Playwright — prévu phase 4.
- La migration 001 utilise `gen_random_uuid()` : exécuter `CREATE EXTENSION pgcrypto`
  si erreur sur Postgres < 13.
- `docker-compose.yml` et `.env.example` contiennent un mot de passe de
  démonstration (`changeme`) — à remplacer par un secret store en production
  (TODO documenté).
- Warning pytest non bloquant : `StarletteDeprecationWarning` (TestClient httpx)
  — à résoudre lors d'une montée de version FastAPI/Starlette.
