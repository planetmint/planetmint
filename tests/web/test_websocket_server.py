# Copyright © 2020 Interplanetary Database Association e.V.,
# Planetmint and IPDB software contributors.
# SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
# Code is Apache-2.0 and docs are CC-BY-4.0
import aiohttp
import asyncio
import json
import queue
import threading
import pytest
import random
import time

# from unittest.mock import patch
from transactions.types.assets.create import Create
from transactions.types.assets.transfer import Transfer
from transactions.common import crypto
from transactions.common.crypto import generate_key_pair

# from planetmint import processes
from planetmint.ipc import events  # , POISON_PILL
from planetmint.web.websocket_server import init_app, EVENTS_ENDPOINT, EVENTS_ENDPOINT_BLOCKS
from ipld import multihash, marshal
from planetmint.web.websocket_dispatcher import Dispatcher


def test_eventify_block_works_with_any_transaction():
    alice = generate_key_pair()

    tx = Create.generate([alice.public_key], [([alice.public_key], 1)]).sign([alice.private_key])
    tx_transfer = Transfer.generate(tx.to_inputs(), [([alice.public_key], 1)], asset_ids=[tx.id]).sign(
        [alice.private_key]
    )

    block = {"height": 1, "transactions": [tx, tx_transfer]}

    expected_events = [
        {"height": 1, "asset_ids": [tx.id], "transaction_id": tx.id},
        {"height": 1, "asset_ids": [tx_transfer.assets[0]["id"]], "transaction_id": tx_transfer.id},
    ]

    for event, expected in zip(Dispatcher.eventify_block(block), expected_events):
        assert event == expected


def test_simplified_block_works():
    alice = generate_key_pair()

    tx = Create.generate([alice.public_key], [([alice.public_key], 1)]).sign([alice.private_key])
    tx_transfer = Transfer.generate(tx.to_inputs(), [([alice.public_key], 1)], asset_ids=[tx.id]).sign(
        [alice.private_key]
    )

    block = {
        "height": 1,
        "hash": "27E2D48AFA5E4B7FF26AA9C84B5CFCA2A670DBD297740053C0D177EB18962B09",
        "transactions": [tx, tx_transfer],
    }

    expected_event = {
        "height": 1,
        "hash": "27E2D48AFA5E4B7FF26AA9C84B5CFCA2A670DBD297740053C0D177EB18962B09",
        "transaction_ids": [tx.id, tx_transfer.id],
    }

    blk_event = Dispatcher.simplified_block(block)
    assert blk_event == expected_event


@pytest.mark.asyncio
async def test_websocket_block_event(aiohttp_client):
    user_priv, user_pub = crypto.generate_key_pair()
    tx = Create.generate([user_pub], [([user_pub], 1)])
    tx = tx.sign([user_priv])

    app = init_app(None)
    client = await aiohttp_client(app)
    ws = await client.ws_connect(EVENTS_ENDPOINT_BLOCKS)
    block = {
        "height": 1,
        "hash": "27E2D48AFA5E4B7FF26AA9C84B5CFCA2A670DBD297740053C0D177EB18962B09",
        "transactions": [tx],
    }
    block_event = events.Event(events.EventTypes.BLOCK_VALID, block)
    blk_source = Dispatcher.get_queue_on_demand(app, "blk_source")
    tx_source = Dispatcher.get_queue_on_demand(app, "tx_source")
    await blk_source.put(block_event)

    result = await ws.receive()
    json_result = json.loads(result.data)
    assert json_result["height"] == block["height"]
    assert json_result["hash"] == block["hash"]
    assert len(json_result["transaction_ids"]) == 1
    assert json_result["transaction_ids"][0] == tx.id

    await blk_source.put(events.POISON_PILL)
    await tx_source.put(events.POISON_PILL)


@pytest.mark.asyncio
async def test_websocket_transaction_event(aiohttp_client):
    user_priv, user_pub = crypto.generate_key_pair()
    tx = Create.generate([user_pub], [([user_pub], 1)])
    tx = tx.sign([user_priv])

    myapp = init_app(None)
    client = await aiohttp_client(myapp)
    ws = await client.ws_connect(EVENTS_ENDPOINT)
    block = {"height": 1, "transactions": [tx]}
    blk_source = Dispatcher.get_queue_on_demand(myapp, "blk_source")
    tx_source = Dispatcher.get_queue_on_demand(myapp, "tx_source")
    block_event = events.Event(events.EventTypes.BLOCK_VALID, block)

    await tx_source.put(block_event)

    for tx in block["transactions"]:
        result = await ws.receive()
        json_result = json.loads(result.data)
        assert json_result["transaction_id"] == tx.id
        # Since the transactions are all CREATEs, asset id == transaction id
        assert json_result["asset_ids"] == [tx.id]
        assert json_result["height"] == block["height"]

    await blk_source.put(events.POISON_PILL)
    await tx_source.put(events.POISON_PILL)


@pytest.mark.asyncio
async def test_websocket_string_event(aiohttp_client):
    myapp = init_app(None)
    client = await aiohttp_client(myapp)
    ws = await client.ws_connect(EVENTS_ENDPOINT)

    blk_source = Dispatcher.get_queue_on_demand(myapp, "blk_source")
    tx_source = Dispatcher.get_queue_on_demand(myapp, "tx_source")

    await tx_source.put("hack")
    await tx_source.put("the")
    await tx_source.put("planet!")

    result = await ws.receive()
    assert result.data == "hack"

    result = await ws.receive()
    assert result.data == "the"

    result = await ws.receive()
    assert result.data == "planet!"

    await blk_source.put(events.POISON_PILL)
    await tx_source.put(events.POISON_PILL)


@pytest.mark.skip("Processes are not stopping properly, and the whole test suite would hang")
def test_integration_from_webapi_to_websocket(monkeypatchonkeypatch, client, loop):
    # XXX: I think that the `pytest-aiohttp` plugin is sparkling too much
    # magic in the `asyncio` module: running this test without monkey-patching
    # `asycio.get_event_loop` (and without the `loop` fixture) raises a:
    #     RuntimeError: There is no current event loop in thread 'MainThread'.
    #
    # That's pretty weird because this test doesn't use the pytest-aiohttp
    # plugin explicitely.
    monkeypatch.setattr("asyncio.get_event_loop", lambda: loop)

    # TODO processes does not exist anymore, when reactivating this test it
    # will fail because of this
    # Start Planetmint
    processes.start()

    loop = asyncio.get_event_loop()

    time.sleep(1)

    ws_url = client.get("http://localhost:9984/api/v1/").json["_links"]["streams_v1"]

    # Connect to the WebSocket endpoint
    session = aiohttp.ClientSession()
    ws = loop.run_until_complete(session.ws_connect(ws_url))

    # Create a keypair and generate a new asset
    user_priv, user_pub = crypto.generate_key_pair()
    assets = [{"data": multihash(marshal({"random": random.random()}))}]
    tx = Create.generate([user_pub], [([user_pub], 1)], assets=assets)
    tx = tx.sign([user_priv])
    # Post the transaction to the Planetmint Web API
    client.post("/api/v1/transactions/", data=json.dumps(tx.to_dict()))

    result = loop.run_until_complete(ws.receive())
    json_result = json.loads(result.data)
    assert json_result["transaction_id"] == tx.id
