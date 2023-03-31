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
#import threading
import aiohttp
import multiprocessing

from uuid import uuid4
from concurrent.futures import CancelledError
from planetmint.config import Config
from planetmint.web.websocket_dispatcher import Dispatcher
#from asyncer import asyncify

logger = logging.getLogger(__name__)
EVENTS_ENDPOINT = "/api/v1/streams/valid_transactions"
EVENTS_ENDPOINT_BLOCKS = "/api/v1/streams/valid_blocks"


async def access_queue(app):
    #global app
    in_queue = app["event_source"]
    tx_source = Dispatcher.get_queue_on_demand(app,"tx_source" )
    blk_source = Dispatcher.get_queue_on_demand(app,"blk_source" )
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
                raise e #await asyncio.sleep(1)
    except asyncio.CancelledError as e:
        logger.debug(f"REROUTING Cancelled : {e}")
        pass
    #except Exception as e:
    #    logger.debug(f"REROUTING Exception: {e}")
    #finally:
    #    return



#async def reroute_message(app):
#    """Bridge between a synchronous multiprocessing queue
#    and an asynchronous asyncio queue.
#
#    Args:
#        in_queue (multiprocessing.Queue): input queue
#        out_queue (asyncio.Queue): output queue
#    """
#    in_queue = app["event_source"]
#    tx_source = app["tx_source"]
#    blk_source = app["blk_source"]
#    #loop = app["loop"]
#    i = 0
#    while True:
#        i = i + 1
#        #value = await asyncify( in_queue.get() )
#        #logger.debug(f"REROUTING: {i}")
#        #tx_source.put( value)
#        #blk_source.put( value)
#        #loop.call_soon_threadsafe(tx_source.put_nowait, value)
#        #loop.call_soon_threadsafe(blk_source.put_nowait, value)


def _multiprocessing_to_asyncio(in_queue, out_queue1, out_queue2, loop):
    """Bridge between a synchronous multiprocessing queue
    and an asynchronous asyncio queue.

    Args:
        in_queue (multiprocessing.Queue): input queue
        out_queue (asyncio.Queue): output queue
    """

    while True:
        value = in_queue.get_nowait()
        logger.debug(f"REROUTING: {value}")
        logger.debug(f"REROUTING: {loop}")
        loop.call_soon_threadsafe(out_queue1.put_nowait, value)
        loop.call_soon_threadsafe(out_queue2.put_nowait, value)


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
    app["task2"]  = asyncio.create_task(tx_dispatcher.publish(app), name="tx")
    
    app["task3"]  = asyncio.create_task(access_queue(app), name="router")
    
    
async def cleanup_background_tasks(app):
    app["task1"].cancel()
    app["task2"].cancel()
    app["task3"].cancel()
    await app["task3"]
    await app["task1"]
    await app["task2"]
    
async def start_cleanup_all_background_tasks(app):
    blk_dispatcher = app["blk_dispatcher"]
    app["task1"] = asyncio.create_task(blk_dispatcher.publish(app), name="blk")

    tx_dispatcher = app["tx_dispatcher"]
    app["task2"]  = asyncio.create_task(tx_dispatcher.publish(app), name="tx")
    
    app["task3"]  = asyncio.create_task(access_queue(app), name="router")
    
    #yield 
    
    app["task1"].cancel()
    app["task2"].cancel()
    app["task3"].cancel()
    await app["task3"]
    await app["task1"]
    await app["task2"]
    
    
    #await asyncio.gather(app["task1"], app["task2"], 
    #                     app["task3"],
    #                     return_exceptions=True)
    
#async def background_task_blk_dispatcher(app):
#    blk_dispatcher = app["blk_dispatcher"]
#    app["blk_bkg_task"] = asyncio.create_task(blk_dispatcher.publish(), name="blk")
#
#    yield
#    
#    app["blk_bkg_task"].cancel()
#    await app["blk_bkg_task"]
#
#async def background_task_tx_dispatcher(app):
#    tx_dispatcher = app["tx_dispatcher"]
#    app["tx_bkg_task"]  = asyncio.create_task(tx_dispatcher.publish(), name="tx")
#
#    yield
#    
#    app["tx_bkg_task"].cancel()
#    await app["tx_bkg_task"]
#
#async def background_task_route_dispatcher(app):
#    app["route_bkg_task"]  = asyncio.create_task(access_queue(), name="router")
#
#    yield
#    
#    app["route_bkg_task"].cancel()
#    await app["route_bkg_task"]
    
global app

def init_app(sync_event_source):
    """Create and start the WebSocket server."""
    global app
    #global event_src
    app = aiohttp.web.Application()
    
    # queue definition

    #tx_source = asyncio.Queue()
    #blk_source = asyncio.Queue()
    #app["tx_source"] = tx_source
    #app["blk_source"] = blk_source
    
    app["event_source"] = sync_event_source
    
    #dispatchers
    app["tx_dispatcher"] = Dispatcher("tx")
    app["blk_dispatcher"] = Dispatcher("blk")
    
    # routes
    app.router.add_get(EVENTS_ENDPOINT, websocket_tx_handler)
    app.router.add_get(EVENTS_ENDPOINT_BLOCKS, websocket_blk_handler)


    
    
    #app.on_startup.append(start_background_tasks)

    app.on_startup.append( start_background_tasks )
    #app.cleanup_ctx.append(cleanup_background_tasks)
    #app.cleanup_ctx.append(background_task_route_dispatcher)
    #app.cleanup_ctx.append(background_task_tx_dispatcher)
    #app.cleanup_ctx.append(background_task_blk_dispatcher)
    
    #app = init_app(app, tx_source, blk_source)

    #bridge = threading.Thread(
    #    target=_multiprocessing_to_asyncio,
    #    args=(sync_event_source, tx_source, blk_source, asyncio.get_event_loop()),
    #    daemon=True,
    #)
    #bridge.start()
    return app
    
    
global event_src

def start(sync_event_source):
    #global event_src
    #event_src=sync_event_source
    #app = asyncio.run(init_app(sync_event_source))
    app = init_app(sync_event_source)
    aiohttp.web.run_app(app, host=Config().get()["wsserver"]["host"], port=Config().get()["wsserver"]["port"])