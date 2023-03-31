# Copyright © 2020 Interplanetary Database Association e.V.,
# Planetmint and IPDB software contributors.
# SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
# Code is Apache-2.0 and docs are CC-BY-4.0

"""WebSocket server for the Planetmint Event Stream API."""

# NOTE
#
# This module contains some functions and utilities that might belong to other
# modules. For now, I prefer to keep everything in this module. Why? Because
# those functions are needed only here.
#
# When we will extend this part of the project and we find that we need those
# functionalities elsewhere, we can start creating new modules and organizing
# things in a better way.


import asyncio
import logging
import threading
import aiohttp

from uuid import uuid4
from concurrent.futures import CancelledError
from planetmint.config import Config
from planetmint.web.websocket_dispatcher import Dispatcher
from asyncer import asyncify

logger = logging.getLogger(__name__)
EVENTS_ENDPOINT = "/api/v1/streams/valid_transactions"
EVENTS_ENDPOINT_BLOCKS = "/api/v1/streams/valid_blocks"


def reroute_message(app):
    """Bridge between a synchronous multiprocessing queue
    and an asynchronous asyncio queue.

    Args:
        in_queue (multiprocessing.Queue): input queue
        out_queue (asyncio.Queue): output queue
    """
    in_queue = app["event_source"]
    tx_source = app["tx_source"]
    blk_source = app["blk_source"]
    loop = app["loop"]
    while True:
        value = in_queue.get()
        # tx_source.put( value)
        # blk_source.put( value)
        loop.call_soon_threadsafe(tx_source.put_nowait, value)
        loop.call_soon_threadsafe(blk_source.put_nowait, value)


def _multiprocessing_to_asyncio(in_queue, out_queue1, out_queue2, loop):
    """Bridge between a synchronous multiprocessing queue
    and an asynchronous asyncio queue.

    Args:
        in_queue (multiprocessing.Queue): input queue
        out_queue (asyncio.Queue): output queue
    """

    while True:
        value = in_queue.get()
        logger.debug(f"REROUTING: {value}")
        asyncio.call_soon_threadsafe(out_queue1.put_nowait, value)
        asyncio.call_soon_threadsafe(out_queue2.put_nowait, value)


async def websocket_tx_handler(request):
    """Handle a new socket connection."""

    logger.debug("New TX websocket connection.")
    websocket = aiohttp.web.WebSocketResponse()
    await websocket.prepare(request)
    uuid = uuid4()
    request.app["tx_dispatcher"].subscribe(uuid, websocket)

    while True:
        # Consume input buffer
        try:
            msg = await websocket.receive()
            logger.debug(f"TX HANDLER: {msg}")
        except RuntimeError as e:
            logger.debug("Websocket exception: %s", str(e))
            break
        except CancelledError:
            logger.debug("Websocket closed")
            break
        if msg.type == aiohttp.WSMsgType.CLOSED:
            logger.debug("Websocket closed")
            break
        elif msg.type == aiohttp.WSMsgType.ERROR:
            logger.debug("Websocket exception: %s", websocket.exception())
            break

    request.app["tx_dispatcher"].unsubscribe(uuid)
    return websocket


async def websocket_blk_handler(request):
    """Handle a new socket connection."""

    logger.debug("New BLK websocket connection.")
    websocket = aiohttp.web.WebSocketResponse()
    await websocket.prepare(request)
    uuid = uuid4()
    request.app["blk_dispatcher"].subscribe(uuid, websocket)

    while True:
        # Consume input buffer
        try:
            msg = await websocket.receive()
            logger.debug(f"BLK HANDLER: {msg}")
        except RuntimeError as e:
            logger.debug("Websocket exception: %s", str(e))
            break
        except CancelledError:
            logger.debug("Websocket closed")
            break
        if msg.type == aiohttp.WSMsgType.CLOSED:
            logger.debug("Websocket closed")
            break
        elif msg.type == aiohttp.WSMsgType.ERROR:
            logger.debug("Websocket exception: %s", websocket.exception())
            break

    request.app["blk_dispatcher"].unsubscribe(uuid)
    return websocket


async def init_app(app, tx_source, blk_source):
    """Init the application server.

    Return:
        An aiohttp application.
    """

    blk_dispatcher = Dispatcher(blk_source, "blk")
    tx_dispatcher = Dispatcher(tx_source, "tx")

    # Schedule the dispatcher
    asyncio.create_task(blk_dispatcher.publish(), name="blk")
    asyncio.create_task(tx_dispatcher.publish(), name="tx")

    app["tx_dispatcher"] = tx_dispatcher
    app["blk_dispatcher"] = blk_dispatcher
    app.router.add_get(EVENTS_ENDPOINT, websocket_tx_handler)
    app.router.add_get(EVENTS_ENDPOINT_BLOCKS, websocket_blk_handler)

    app["tx_source"] = tx_source
    app["blk_source"] = blk_source
    # app["loop"]=loop

    return app


def start(sync_event_source):
    """Create and start the WebSocket server."""

    tx_source = asyncio.Queue()
    blk_source = asyncio.Queue()

    app = aiohttp.web.Application()
    app["event_source"] = sync_event_source
    app = init_app(app, tx_source, blk_source)

    bridge = threading.Thread(
        target=_multiprocessing_to_asyncio,
        args=(sync_event_source, tx_source, blk_source, asyncio.get_event_loop()),
        daemon=True,
    )
    bridge.start()

    aiohttp.web.run_app(app, host=Config().get()["wsserver"]["host"], port=Config().get()["wsserver"]["port"])
