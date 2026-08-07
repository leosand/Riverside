# Vérification & Validation (V&V) — Riverside v0.3.0

## Méthodologie

- **Vérification** : le système est-il construit correctement ? (tests unitaires,
  intégration, E2E, lint, schéma)
- **Validation** : construit-on le bon système ? (exactitude numérique des indices,
  comportement métier des alertes, parcours utilisateur complet)

## Matrice de traçabilité exigences → tests

| Exigence | Vérifiée par | Statut |
|---|---|---|
| NDVI = (NIR−R)/(NIR+R), borné [−1,1] | `tests/test_ndvi.py::test_ndvi_known_values` (valeur connue 0.6) | ✅ |
| Division par zéro → NaN | `test_ndvi_zero_denominator_is_nan` | ✅ |
| Scène 100 % nuageuse → erreur explicite | `test_summarize_empty_raises`, E2E `test_e2e_all_cloud_scene_raises` | ✅ |
| Seuil réglementaire → alerte warning/critical | `tests/test_alerts.py` (3 cas de bord) | ✅ |
| Persistance transactionnelle des alertes | `tests/test_repository.py` | ✅ |
| Pas de dérive schéma vs migration SQL | `test_table_matches_migration_columns` | ✅ |
| Acquittement idempotent-safe | `tests/test_acknowledge.py` (inconnu, double) | ✅ |
| Webhook n8n best-effort, jamais bloquant | `tests/test_notify.py` | ✅ |
| API dégradée gracieusement sans DB | `test_evaluate_alert_critical_without_db_still_200` | ✅ |
| Erreurs RFC 7807 (400/404/503) | `tests/test_api.py`, E2E `test_e2e_alert_lifecycle` | ✅ |
| Chaîne complète scène→composite→NDVI→série→alerte | `tests/e2e/test_pipeline_e2e.py` (scène synthétique) | ✅ |
| Cycle API complet evaluate→open→ack→open vide | `tests/e2e/test_api_e2e.py` | ✅ |

## Validation numérique (E2E synthétique)

La scène synthétique (red=2000, nir=8000, échelle 1e4) produit un NDVI attendu
de **0.6** ; le test E2E vérifie :
1. Le composite médian exclut bien les pixels SCL=8 (nuages) de la date t1.
2. `ndvi_mean ≈ 0.6` (tolérance 1e-4) — exactitude de bout en bout.
3. `p10 ≤ mean ≤ p90` — cohérence des quantiles.
4. NDVI 0.20 vs seuil 0.30 → sévérité `critical` → persistance → acquittement.

## Exécution

```bash
pytest tests/ -v          # unitaires + intégration + E2E (tout offline)
ruff check src tests      # lint (CI)
```

La CI GitHub Actions (`.github/workflows/ci.yml`) rejoue lint + tests à chaque
push/PR sur Python 3.12.

## Limites connues / Known limitations

- Les appels STAC réels (réseau) ne sont pas couverts par les tests — à mocker
  avec `responses`/`respx` en phase 4 (test d'intégration contractuelle).
- Le frontend n'a pas encore de tests Playwright — prévu phase 4.
- La migration 001 utilise `gen_random_uuid()` : exécuter `CREATE EXTENSION pgcrypto`
  si erreur sur Postgres < 13.
