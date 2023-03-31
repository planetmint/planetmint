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
import aiohttp

from uuid import uuid4
from concurrent.futures import CancelledError
from planetmint.config import Config
from planetmint.web.websocket_dispatcher import Dispatcher

logger = logging.getLogger(__name__)
EVENTS_ENDPOINT = "/api/v1/streams/valid_transactions"
EVENTS_ENDPOINT_BLOCKS = "/api/v1/streams/valid_blocks"


async def access_queue(app):
    if app["event_source"] == None:
        return
    in_queue = app["event_source"]
    tx_source = Dispatcher.get_queue_on_demand(app, "tx_source")
    blk_source = Dispatcher.get_queue_on_demand(app, "blk_source")
    logger.debug(f"REROUTING CALLED")
    try:
        while True:
            try:
                if not in_queue.empty():
                    item = in_queue.get_nowait()
                    logger.debug(f"REROUTING: {item}")
                    await tx_source.put(item)
                    await blk_source.put(item)
                else:
                    await asyncio.sleep(1)
            except Exception as e:
                logger.debug(f"REROUTING wait exception : {e}")
                raise e  # await asyncio.sleep(1)
    except asyncio.CancelledError as e:
        logger.debug(f"REROUTING Cancelled : {e}")
        pass


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


async def start_background_tasks(app):
    blk_dispatcher = app["blk_dispatcher"]
    app["task1"] = asyncio.create_task(blk_dispatcher.publish(app), name="blk")

    tx_dispatcher = app["tx_dispatcher"]
    app["task2"] = asyncio.create_task(tx_dispatcher.publish(app), name="tx")

    app["task3"] = asyncio.create_task(access_queue(app), name="router")


def init_app(sync_event_source):
    """Create and start the WebSocket server."""
    app = aiohttp.web.Application()
    app["event_source"] = sync_event_source

    # dispatchers
    app["tx_dispatcher"] = Dispatcher("tx")
    app["blk_dispatcher"] = Dispatcher("blk")

    # routes
    app.router.add_get(EVENTS_ENDPOINT, websocket_tx_handler)
    app.router.add_get(EVENTS_ENDPOINT_BLOCKS, websocket_blk_handler)

    app.on_startup.append(start_background_tasks)
    return app


def start(sync_event_source):
    app = init_app(sync_event_source)
    aiohttp.web.run_app(app, host=Config().get()["wsserver"]["host"], port=Config().get()["wsserver"]["port"])
