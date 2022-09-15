# Copyright © 2020 Interplanetary Database Association e.V.,
# Planetmint and IPDB software contributors.
# SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
# Code is Apache-2.0 and docs are CC-BY-4.0

import pytest
from planetmint.transactions.types.assets.create import Create
from ipld import marshal, multihash

ASSETS_ENDPOINT = "/api/v1/assets/"


def test_get_assets_with_empty_text_search(client):
    res = client.get(ASSETS_ENDPOINT + "?search=")
    assert res.json == {"status": 400, "message": "text_search cannot be empty"}
    assert res.status_code == 400


def test_get_assets_with_missing_text_search(client):
    res = client.get(ASSETS_ENDPOINT)
    assert res.status_code == 400


@pytest.mark.bdb
def test_get_assets_tendermint(client, b, alice):

    # test returns empty list when no assets are found
    res = client.get(ASSETS_ENDPOINT + "?search=abc")
    assert res.json == []
    assert res.status_code == 200

    # create asset
    asset = {"data": multihash(marshal({"msg": "abc"}))}
    tx = Create.generate([alice.public_key], [([alice.public_key], 1)], asset=asset).sign([alice.private_key])

    b.store_bulk_transactions([tx])

    # test that asset is returned
    res = client.get(ASSETS_ENDPOINT + "?search=" + asset["data"])
    assert res.status_code == 200
    assert len(res.json) == 1
    assert res.json[0] == {"data": asset["data"], "id": tx.id}


@pytest.mark.bdb
def test_get_assets_limit_tendermint(client, b, alice):

    # create two assets
    asset1 = {"data": multihash(marshal({"msg": "abc 1"}))}
    asset2 = {"data": multihash(marshal({"msg": "abc 2"}))}
    tx1 = Create.generate([alice.public_key], [([alice.public_key], 1)], asset=asset1).sign([alice.private_key])
    tx2 = Create.generate([alice.public_key], [([alice.public_key], 1)], asset=asset2).sign([alice.private_key])

    b.store_bulk_transactions([tx1])
    b.store_bulk_transactions([tx2])

    # test that both assets are returned without limit
    res = client.get(ASSETS_ENDPOINT + "?search=" + asset1["data"])
    assert res.status_code == 200
    assert len(res.json) == 1

    # test that only one asset is returned when using limit=1
    res = client.get(ASSETS_ENDPOINT + "?search=" + asset1["data"] + "&limit=1")
    assert res.status_code == 200
    assert len(res.json) == 1
