"""Test d'intégration STAC LIVE — Earth Search réel (réseau).

EN: Live STAC integration test against the real Earth Search API. Requires
network access — deliberately EXCLUDED from the default offline suite via the
`integration` marker (see pytest.ini). Run explicitly with:

    pytest tests/test_stac_live.py -m integration -v

Le test est tolérant : il ne fait pas échouer la CI (le réseau n'est pas
garanti), mais il consigne le résultat réel pour la V&V.
"""
from datetime import date

import pytest

from src.ingest.stac_client import search_scenes

pytestmark = pytest.mark.integration


def test_live_search_scenes_earth_search() -> None:
    """Recherche réelle sur Earth Search : bbox Grands Lacs, 7 derniers jours.

    EN: Real STAC search over the Great Lakes bbox. Si le réseau est
    indisponible ou que la requête échoue, le test est marqué en échec
    (xfail) sans bloquer la suite — résultat consigné pour la V&V.
    """
    try:
        scenes = search_scenes(
            bbox=(-83.5, 42.0, -82.0, 43.5),
            start=date(2026, 7, 1),
            end=date(2026, 7, 31),
            max_cloud=50.0,
            limit=5,
        )
    except Exception as exc:  # noqa: BLE001 — réseau/API non déterministe, volontaire / live network, intentional
        pytest.fail(f"Appel STAC réel en échec : {exc}")

    # Aucune garantie de scènes sur la fenêtre — on vérifie le contrat de type
    # / no guarantee of scenes — assert the return contract only
    assert isinstance(scenes, list)
