# Copyright © 2020 Interplanetary Database Association e.V.,
# Planetmint and IPDB software contributors.
# SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
# Code is Apache-2.0 and docs are CC-BY-4.0

import asyncio
import json
import queue
import threading

# from unittest.mock import patch
from planetmint.transactions.types.assets.create import Create
from planetmint.transactions.types.assets.transfer import Transfer
from ipld import multihash, marshal

import pytest


class MockWebSocket:
    def __init__(self):
        self.received = []

    def send_str(self, s):
        self.received.append(s)


def test_eventify_block_works_with_any_transaction():
    from planetmint.web.websocket_dispatcher import Dispatcher
    from planetmint.transactions.common.crypto import generate_key_pair

    alice = generate_key_pair()

    tx = Create.generate([alice.public_key], [([alice.public_key], 1)]).sign([alice.private_key])
    tx_transfer = Transfer.generate(tx.to_inputs(), [([alice.public_key], 1)], asset_id=tx.id).sign(
        [alice.private_key]
    )

    block = {"height": 1, "transactions": [tx, tx_transfer]}

    expected_events = [
        {"height": 1, "asset_id": tx.id, "transaction_id": tx.id},
        {"height": 1, "asset_id": tx_transfer.asset["id"], "transaction_id": tx_transfer.id},
    ]

    for event, expected in zip(Dispatcher.eventify_block(block), expected_events):
        assert event == expected


def test_simplified_block_works():
    from planetmint.web.websocket_dispatcher import Dispatcher
    from planetmint.transactions.common.crypto import generate_key_pair

    alice = generate_key_pair()

    tx = Create.generate([alice.public_key], [([alice.public_key], 1)]).sign([alice.private_key])
    tx_transfer = Transfer.generate(tx.to_inputs(), [([alice.public_key], 1)], asset_id=tx.id).sign(
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
async def test_bridge_sync_async_queue(event_loop):
    from planetmint.web.websocket_server import _multiprocessing_to_asyncio

    sync_queue = queue.Queue()
    async_queue = asyncio.Queue(loop=event_loop)
    async_queue2 = asyncio.Queue(loop=event_loop)

    bridge = threading.Thread(
        target=_multiprocessing_to_asyncio, args=(sync_queue, async_queue, async_queue2, event_loop), daemon=True
    )
    bridge.start()

    sync_queue.put("fahren")
    sync_queue.put("auf")
    sync_queue.put("der")
    sync_queue.put("Autobahn")

    result = await async_queue.get()
    assert result == "fahren"

    result = await async_queue.get()
    assert result == "auf"

    result = await async_queue.get()
    assert result == "der"

    result = await async_queue.get()
    assert result == "Autobahn"

    print(f" queue ({async_queue.qsize()}): {async_queue} ")
    assert async_queue.qsize() == 0


# TODO: fix the test and uncomment it
# @patch('threading.Thread')
# @patch('aiohttp.web.run_app')
# @patch('planetmint.web.websocket_server.init_app')
# @patch('asyncio.get_event_loop', return_value='event-loop')
# @patch('asyncio.Queue', return_value='event-queue')
# def test_start_creates_an_event_loop(queue_mock, get_event_loop_mock,
#                                     init_app_mock, run_app_mock,
#                                     thread_mock):
#    from planetmint import config
#    from planetmint.web.websocket_server import start, _multiprocessing_to_asyncio
#
#    start(None)
#    #thread_mock.assert_called_once_with(
#    #    target=_multiprocessing_to_asyncio,
#    #    args=(None, queue_mock.return_value, queue_mock.return_value, get_event_loop_mock.return_value),
#    #    daemon=True,
#    #)
#    thread_mock.return_value.start.assert_called_once_with()
#    init_app_mock.assert_called_with('event-queue', 'event-queue', loop='event-loop')
#    run_app_mock.assert_called_once_with(
#        init_app_mock.return_value,
#        host=config['wsserver']['host'],
#        port=config['wsserver']['port'],
#    )


@pytest.mark.asyncio
async def test_websocket_block_event(aiohttp_client, event_loop):
    from planetmint import events
    from planetmint.web.websocket_server import init_app, EVENTS_ENDPOINT_BLOCKS
    from planetmint.transactions.common import crypto

    user_priv, user_pub = crypto.generate_key_pair()
    tx = Create.generate([user_pub], [([user_pub], 1)])
    tx = tx.sign([user_priv])

    blk_source = asyncio.Queue(loop=event_loop)
    tx_source = asyncio.Queue(loop=event_loop)
    app = init_app(tx_source, blk_source, loop=event_loop)
    client = await aiohttp_client(app)
    ws = await client.ws_connect(EVENTS_ENDPOINT_BLOCKS)
    block = {
        "height": 1,
        "hash": "27E2D48AFA5E4B7FF26AA9C84B5CFCA2A670DBD297740053C0D177EB18962B09",
        "transactions": [tx],
    }
    block_event = events.Event(events.EventTypes.BLOCK_VALID, block)

    await blk_source.put(block_event)

    result = await ws.receive()
    json_result = json.loads(result.data)
    assert json_result["height"] == block["height"]
    assert json_result["hash"] == block["hash"]
    assert len(json_result["transaction_ids"]) == 1
    assert json_result["transaction_ids"][0] == tx.id

    await blk_source.put(events.POISON_PILL)


@pytest.mark.asyncio
async def test_websocket_transaction_event(aiohttp_client, event_loop):
    from planetmint import events
    from planetmint.web.websocket_server import init_app, EVENTS_ENDPOINT
    from planetmint.transactions.common import crypto

    user_priv, user_pub = crypto.generate_key_pair()
    tx = Create.generate([user_pub], [([user_pub], 1)])
    tx = tx.sign([user_priv])

    blk_source = asyncio.Queue(loop=event_loop)
    tx_source = asyncio.Queue(loop=event_loop)
    app = init_app(tx_source, blk_source, loop=event_loop)
    client = await aiohttp_client(app)
    ws = await client.ws_connect(EVENTS_ENDPOINT)
    block = {"height": 1, "transactions": [tx]}
    block_event = events.Event(events.EventTypes.BLOCK_VALID, block)

    await tx_source.put(block_event)

    for tx in block["transactions"]:
        result = await ws.receive()
        json_result = json.loads(result.data)
        assert json_result["transaction_id"] == tx.id
        # Since the transactions are all CREATEs, asset id == transaction id
        assert json_result["asset_id"] == tx.id
        assert json_result["height"] == block["height"]

    await tx_source.put(events.POISON_PILL)


@pytest.mark.asyncio
async def test_websocket_string_event(aiohttp_client, event_loop):
    from planetmint.events import POISON_PILL
    from planetmint.web.websocket_server import init_app, EVENTS_ENDPOINT

    blk_source = asyncio.Queue(loop=event_loop)
    tx_source = asyncio.Queue(loop=event_loop)
    app = init_app(tx_source, blk_source, loop=event_loop)
    client = await aiohttp_client(app)
    ws = await client.ws_connect(EVENTS_ENDPOINT)

    await tx_source.put("hack")
    await tx_source.put("the")
    await tx_source.put("planet!")

    result = await ws.receive()
    assert result.data == "hack"

    result = await ws.receive()
    assert result.data == "the"

    result = await ws.receive()
    assert result.data == "planet!"

    await tx_source.put(POISON_PILL)


@pytest.mark.skip("Processes are not stopping properly, and the whole test suite would hang")
def test_integration_from_webapi_to_websocket(monkeypatch, client, loop):
    # XXX: I think that the `pytest-aiohttp` plugin is sparkling too much
    # magic in the `asyncio` module: running this test without monkey-patching
    # `asycio.get_event_loop` (and without the `loop` fixture) raises a:
    #     RuntimeError: There is no current event loop in thread 'MainThread'.
    #
    # That's pretty weird because this test doesn't use the pytest-aiohttp
    # plugin explicitely.
    monkeypatch.setattr("asyncio.get_event_loop", lambda: loop)

    import json
    import random
    import aiohttp

    from planetmint.transactions.common import crypto

    # TODO processes does not exist anymore, when reactivating this test it
    # will fail because of this
    from planetmint import processes

    # Start Planetmint
    processes.start()

    loop = asyncio.get_event_loop()

    import time

    time.sleep(1)

    ws_url = client.get("http://localhost:9984/api/v1/").json["_links"]["streams_v1"]

    # Connect to the WebSocket endpoint
    session = aiohttp.ClientSession()
    ws = loop.run_until_complete(session.ws_connect(ws_url))

    # Create a keypair and generate a new asset
    user_priv, user_pub = crypto.generate_key_pair()
    asset = {"data": multihash(marshal({"random": random.random()}))}
    tx = Create.generate([user_pub], [([user_pub], 1)], asset=asset)
    tx = tx.sign([user_priv])
    # Post the transaction to the Planetmint Web API
    client.post("/api/v1/transactions/", data=json.dumps(tx.to_dict()))

    result = loop.run_until_complete(ws.receive())
    json_result = json.loads(result.data)
    assert json_result["transaction_id"] == tx.id
