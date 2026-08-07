"""Test contractuel STAC — réponse Earth Search minimale mockée (offline).

EN: STAC contract test — search_scenes against a mocked Earth Search response
(responses), proving the client parses items and cloud_cover sorting works
without any network access. Déterministe : aucun appel réseau réel.
"""
from datetime import date, datetime, timezone

import pytest
from pystac import Item, ItemCollection
from responses import RequestsMock
from tenacity import RetryError

from src.ingest.stac_client import SceneSummary, search_scenes

STAC_URL = "https://earth-search.aws.element84.com/v1"

# Catalogue racine minimal annonçant la conformité item-search /
# minimal root catalog advertising the item-search conformance class
CATALOG = {
    "type": "Catalog",
    "stac_version": "1.0.0",
    "id": "mock",
    "description": "mock catalog for contract test",
    "links": [{"rel": "self", "href": STAC_URL}],
    "conformsTo": ["https://api.stacspec.org/v1.0.0/item-search"],
}


def _item(item_id: str, cloud: float, day: int) -> Item:
    """Item STAC minimal / minimal STAC Item (datetime conscient UTC)."""
    return Item(
        id=item_id,
        geometry={"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]]},
        bbox=[0, 0, 1, 1],
        datetime=datetime(2026, 7, day, 10, 30, tzinfo=timezone.utc),
        properties={"eo:cloud_cover": cloud},
    )


def _mock_catalog_and_search(rsps: RequestsMock, items: ItemCollection) -> None:
    """Enregistre les réponses mockées : GET catalogue + POST /search.

    EN: Register mocked responses — root catalog GET and search POST.
    """
    rsps.add(rsps.GET, STAC_URL, json=CATALOG, status=200)
    rsps.add(
        rsps.POST,
        f"{STAC_URL}/search",
        json=items.to_dict(),
        status=200,
    )


def test_search_scenes_parses_mocked_response() -> None:
    """Réponse ItemCollection mockée → SceneSummary parsés correctement.

    EN: Mocked ItemCollection response is parsed into SceneSummary objects.
    L'ordre renvoyé est celui du serveur (le tri `sortby` est un contrat
    serveur, pas client) — le test vérifie le parsing et la requête, pas le tri.
    """
    items = ItemCollection(
        [_item("S2A-cloudy", 18.0, 2), _item("S2A-clear", 4.0, 1)]
    )
    with RequestsMock() as rsps:
        _mock_catalog_and_search(rsps, items)
        scenes = search_scenes(
            (0.0, 0.0, 1.0, 1.0),
            date(2026, 7, 1),
            date(2026, 7, 31),
            max_cloud=20.0,
        )

    assert len(scenes) == 2
    assert all(isinstance(s, SceneSummary) for s in scenes)
    # Parsing fidèle des métadonnées / faithful metadata parsing
    assert {s.item_id for s in scenes} == {"S2A-cloudy", "S2A-clear"}
    assert {s.cloud_cover for s in scenes} == {18.0, 4.0}
    assert {s.acquired_at for s in scenes} == {date(2026, 7, 1), date(2026, 7, 2)}


def test_search_scenes_filters_by_cloud_cover() -> None:
    """Le paramètre query eo:cloud_cover < max_cloud est envoyé dans la requête."""
    items = ItemCollection([_item("S2A-clear", 3.0, 3)])
    with RequestsMock() as rsps:
        _mock_catalog_and_search(rsps, items)
        scenes = search_scenes(
            (0.0, 0.0, 1.0, 1.0),
            date(2026, 7, 1),
            date(2026, 7, 31),
            max_cloud=5.0,
        )
        assert len(rsps.calls) == 2  # GET catalogue + POST search
        body = rsps.calls[-1].request.body.decode()
        assert '"eo:cloud_cover"' in body  # filtre nuage envoyé au serveur
        assert '"lt": 5.0' in body  # valeur max_cloud transmise

    assert [s.item_id for s in scenes] == ["S2A-clear"]


def test_search_scenes_rejects_invalid_date_range() -> None:
    """Intervalle inversé → ValueError (encapsulé par le retry tenacity).

    EN: Inverted date range raises ValueError wrapped in RetryError by the
    tenacity @retry decorator (retries on all exceptions). Le ValueError est
    levé avant tout appel réseau — assertions sur le type d'erreur uniquement.
    """
    with pytest.raises(RetryError):
        search_scenes(
            (0.0, 0.0, 1.0, 1.0),
            date(2026, 7, 31),
            date(2026, 7, 1),
        )
