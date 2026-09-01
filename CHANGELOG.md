# Changelog

## [Unreleased]

- feat(api+web): nom lisible des zones (aoi_name) au lieu de l'UUID brut dans les alertes
- feat(web): alertes au format professionnel â€” jauge de conformitÃ©, mÃ©trique alignÃ©e, AOI complet
- feat(api+web): fenÃªtre glissante Ã©tendue Ã  12 mois â€” graphique et tableau sur la derniÃ¨re annÃ©e
- feat(api+web): fenÃªtre glissante 6 mois â€” graphique et tableau s'ajustent automatiquement aux donnÃ©es rÃ©centes
- ci(web): exclure les tests de dÃ©mo locale (live/verify/screenshots) de la CI â€” dÃ©pendent de l'API + donnÃ©es
- feat(web): layout Ã©lÃ©gant + temps rÃ©el â€” graphique et tableau cÃ´te Ã  cÃ´te, polling 15s
- test(web): tests Playwright rÃ©silients (API prÃ©sente ou absente) â€” rÃ©pare la CI
- feat(api+web): endpoint sÃ©rie NDVI + tableau d'Ã©volution documentÃ© + CORS frontend
- feat(web): description complÃ¨te du projet â€” problÃ¨me, solution, pipeline 6 Ã©tapes, rapports CSR
- docs(README): aperÃ§u du dashboard avec captures d'Ã©cran
- feat(web): dashboard pÃ©dagogique â€” explainer projet + alertes expliquÃ©es + captures d'Ã©cran
- docs(VV): URLs du dashboard â€” frontend :3101, API :8001 (le 404 racine API est normal)
- docs: Ã©chec ingestion rÃ©elle Sentinel-2 (Connection aborted aprÃ¨s 2h45, rÃ©seau instable)
- fix: monter reports_router + adapter NdviSeriesChart au format ndvi-real.json (rÃ©pare CI)
- feat: phase 4b â€” export dashboard NDVI, rapports CSR FR/EN (Ollama optionnel), script TorchGeo, tests + V&V addendum
- feat(web): dashboard visuel avec donnÃ©es rÃ©elles (NDVI Sentinel-2, lac Ontario)
- docs(VV): API Docker opÃ©rationnelle (libexpat fix, 4 builds rÃ©seau)
- docs(VV): statut CI success sur b6aeebd (fix UUID + dÃ©ploiement)
- fix: aoi_id en UUID strict (alignement schÃ©ma Postgres) + dÃ©ploiement Docker
- feat: E2E frontend Playwright, test STAC live, dev-deps sÃ©parÃ©es
- fix: corrections V&V suite exÃ©cution tests â€” 5 erreurs lint rÃ©solues
- feat: phase 3 â€” acknowledge endpoint, job ingestion NDVI, frontend Next.js MapLibre, tests E2E, V&V + docs
- feat: phase 2 â€” CI GitHub Actions, persistance alertes SQLAlchemy, webhook n8n, endpoint alertes ouvertes
- feat: MVP pipeline berges â€” STAC Sentinel-2, cloud removal, NDVI, LSTM, API FastAPI, PostGIS
- Initial commit
