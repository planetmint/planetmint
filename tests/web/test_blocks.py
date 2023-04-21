# Copyright © 2020 Interplanetary Database Association e.V.,
# Planetmint and IPDB software contributors.
# SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
# Code is Apache-2.0 and docs are CC-BY-4.0

import pytest

BLOCKS_ENDPOINT = "/api/v1/blocks/"


@pytest.mark.bdb
@pytest.mark.usefixtures("inputs")
def test_get_latest_block(client):
    res = client.get(BLOCKS_ENDPOINT + "latest")
    assert res.status_code == 200
    assert len(res.json["transaction_ids"]) == 10
    assert res.json["app_hash"] == "hash3"
    assert res.json["height"] == 3


@pytest.mark.bdb
@pytest.mark.usefixtures("inputs")
def test_get_block_returns_404_if_not_found(client):
    res = client.get(BLOCKS_ENDPOINT + "123")
    assert res.status_code == 404

    res = client.get(BLOCKS_ENDPOINT + "123/")
    assert res.status_code == 404

    res = client.get(BLOCKS_ENDPOINT + "latest")
    assert res.status_code == 200

    res = client.get(BLOCKS_ENDPOINT + "latest/")
    assert res.status_code == 200


@pytest.mark.bdb
def test_get_blocks_by_txid_endpoint_returns_empty_list_not_found(client):
    res = client.get(BLOCKS_ENDPOINT + "?transaction_id=")
    assert res.status_code == 404

    res = client.get(BLOCKS_ENDPOINT + "?transaction_id=123")
    assert res.status_code == 404


@pytest.mark.bdb
def test_get_blocks_by_txid_endpoint_returns_400_bad_query_params(client):
    res = client.get(BLOCKS_ENDPOINT)
    assert res.status_code == 400

    res = client.get(BLOCKS_ENDPOINT + "?ts_id=123")
    assert res.status_code == 400
    assert res.json == {
        "message": {
            "transaction_id": "Missing required parameter in the JSON body or the post body or the query string"
        }
    }

    res = client.get(BLOCKS_ENDPOINT + "?transaction_id=123&foo=123")
    assert res.status_code == 400
    assert res.json == {"message": "Unknown arguments: foo"}

    res = client.get(BLOCKS_ENDPOINT + "?transaction_id=123&status=123")
    assert res.status_code == 400
    assert res.json == {"message": "Unknown arguments: status"}


@pytest.mark.bdb
@pytest.mark.usefixtures("inputs")
def test_get_block_by_height(client):
    res = client.get(BLOCKS_ENDPOINT + "3")
    assert res.status_code == 200
    assert len(res.json["transaction_ids"]) == 10
    assert res.json["app_hash"] == "hash3"
    assert res.json["height"] == 3


@pytest.mark.bdb
@pytest.mark.usefixtures("inputs")
def test_get_block_by_transaction_id(client):
    block_res = client.get(BLOCKS_ENDPOINT + "3")
    print(block_res.json)
    tx_id = block_res.json["transaction_ids"][0]
    res = client.get(BLOCKS_ENDPOINT + "?transaction_id=" + tx_id)
    assert res.json["height"] == 3
