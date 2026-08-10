# Addendum V&V — 2026-08-09 (phase 4b)

## État constaté avant intervention (audit du dépôt)

Mesuré via l'historique des commits (lecture directe des fichiers indisponible
dans la session — SHA uniquement) :

| Élément | Statut constaté | Source |
|---|---|---|
| Tests pytest | 34/34 passés | commit `730d630` |
| CI GitHub Actions | SUCCESS sur `b6aeebd` | commit `346df19` |
| Déploiement Docker | API opérationnelle (fix libexpat1) | commit `c8ce274` |
| Playwright frontend | 4 tests (dashboard réel) | commit `6f0bc32` |
| **Gap #1** | `web/public/data/ndvi-real.json` **absent** — le dashboard l'attend | audit arborescence |
| **Gap #2** | Phase 5 (rapports CSR FR/EN, intégration EBP) non démarrée | roadmap README |
| **Gap #3** | Fine-tuning TorchGeo non démarré | roadmap phase 4 |

## Corrections et implémentations de ce lot

| # | Livrable | Type | Détail |
|---|---|---|---|
| 1 | `src/pipeline/export_dashboard.py` + `scripts/export_ndvi_json.py` | Gap #1 | Export `ndvi_series` → JSON dashboard. SQL direct (`sqlalchemy.text`) pour ne pas dépendre des refactors internes. Schéma documenté = contrat |
| 2 | `web/public/data/ndvi-real.json` | Gap #1 | **Placeholder synthétique explicitement étiqueté** (`meta.source: synthetic_placeholder`, avertissement FR/EN). Aucune mesure fabriquée : à régénérer via le script après un run réel du pipeline |
| 3 | `src/reports/` (csr_context + ollama_client) | Gap #2 | Rapport CSR factuel bilingue FR/EN (zéro LLM requis) + narrative Ollama locale optionnelle (best-effort, None si désactivée) |
| 4 | `src/api/reports_router.py` | Gap #2 | `GET /api/v1/reports/csr`. **Routeur séparé volontairement** : monter dans `main.py` via `app.include_router(...)` — évite de réécrire en aveugle les correctifs UUID/Annotated existants |
| 5 | `scripts/finetune_segmentation.py` | Gap #3 | Squelette documenté TorchGeo (poids S2 pré-entraînés, split spatial, GPU 12 Go) — non exécutable tant que le dataset d'annotation n'existe pas |
| 6 | `tests/test_reports.py`, `tests/test_export_dashboard.py` | V&V | 9 tests offline ajoutés (suite attendue : 43) |

## Action manuelle requise (une ligne)

Dans `src/api/main.py`, ajouter :

```python
from src.api.reports_router import router as reports_router
app.include_router(reports_router)
```

Cette modification n'a PAS été poussée automatiquement : le fichier a évolué
localement (UUID strict, Annotated) et sa réécriture à distance aurait risqué
une régression. Après montage, ajouter un test `GET /api/v1/reports/csr` avec
SQLite injecté (même pattern que `tests/e2e/test_api_e2e.py`).

## Vérification à exécuter

```bash
pip install -r requirements-dev.txt
pytest tests/ -v            # attendu : 43 tests, tout offline
ruff check src tests
cd web && npx tsc --noEmit && npm run test:e2e
```

## Anti-fabrication / honnêteté des données

- Le placeholder JSON déclare `synthetic_placeholder` dans son contenu — le
  dashboard l'affiche sans prétendre à des mesures réelles.
- Aucune valeur NDVI réelle n'a pu être calculée en session : l'accès STAC
  Earth Search était bloqué (SSL) depuis l'environnement d'exécution.
- Les statuts CI/tests cités proviennent des messages de commit, pas d'une
  ré-exécution — à re-valider localement (commandes ci-dessus).
