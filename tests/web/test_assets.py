# Copyright © 2020 Interplanetary Database Association e.V.,
# Planetmint and IPDB software contributors.
# SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
# Code is Apache-2.0 and docs are CC-BY-4.0

import pytest

from transactions.types.assets.create import Create
from ipld import marshal, multihash


ASSETS_ENDPOINT = "/api/v1/assets/"


@pytest.mark.bdb
def test_get_assets_tendermint(client, b, alice):
    # create asset
    assets = [{"data": multihash(marshal({"msg": "abc"}))}]
    tx = Create.generate([alice.public_key], [([alice.public_key], 1)], assets=assets).sign([alice.private_key])

    b.models.store_bulk_transactions([tx])

    res = client.get(ASSETS_ENDPOINT + assets[0]["data"])
    assert res.status_code == 200
    assert len(res.json) == 1
    assert res.json[0] == {"data": assets[0]["data"]}


@pytest.mark.bdb
def test_get_assets_tendermint_limit(client, b, alice, bob):
    # create assets
    assets = [{"data": multihash(marshal({"msg": "abc"}))}]
    tx_1 = Create.generate([alice.public_key], [([alice.public_key], 1)], assets=assets).sign([alice.private_key])
    tx_2 = Create.generate([bob.public_key], [([bob.public_key], 1)], assets=assets).sign([bob.private_key])

    b.models.store_bulk_transactions([tx_1, tx_2])

    res = client.get(ASSETS_ENDPOINT + assets[0]["data"] + "?limit=1")
    assert res.status_code == 200
    assert len(res.json) == 1
    assert res.json[0] == {"data": assets[0]["data"]}
