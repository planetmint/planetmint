# Copyright © 2020 Interplanetary Database Association e.V.,
# Planetmint and IPDB software contributors.
# SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
# Code is Apache-2.0 and docs are CC-BY-4.0

import json
import logging
import asyncio

from planetmint.ipc.events import EventTypes
from planetmint.ipc.events import POISON_PILL
from planetmint.utils.python import is_above_py39

logger = logging.getLogger(__name__)


class Dispatcher:
    """Dispatch events to websockets.

    This class implements a simple publish/subscribe pattern.
    """

    def __init__(self, type="tx"):
        """Create a new instance.

        Args:
            type: a string identifier.
        """

        self.subscribers = {}
        self.type = type

    def subscribe(self, uuid, websocket):
        """Add a websocket to the list of subscribers.

        Args:
            uuid (str): a unique identifier for the websocket.
            websocket: the websocket to publish information.
        """

        self.subscribers[uuid] = websocket

    def unsubscribe(self, uuid):
        """Remove a websocket from the list of subscribers.

        Args:
            uuid (str): a unique identifier for the websocket.
        """

        del self.subscribers[uuid]

    @staticmethod
    def simplified_block(block):
        txids = []
        for tx in block["transactions"]:
            txids.append(tx.id)
        return {"height": block["height"], "hash": block["hash"], "transaction_ids": txids}

    @staticmethod
    def get_queue_on_demand(app, queue_name: str):
        if queue_name not in app:
            logging.debug(f"creating queue: {queue_name}")
            if is_above_py39():
                app[queue_name] = asyncio.Queue()
            else:
                get_loop = asyncio.get_event_loop()
                app[queue_name] = asyncio.Queue(loop=get_loop)

        return app[queue_name]

    @staticmethod
    def eventify_block(block):
        for tx in block["transactions"]:
            asset_ids = []
            if isinstance(tx.assets, dict):
                asset_ids.append(tx.assets)
            elif isinstance(tx.assets, list):
                for asset in tx.assets:
                    asset_ids.append(asset.get("id", tx.id))
            else:
                asset_ids = [tx.id]
            yield {"height": block["height"], "asset_ids": asset_ids, "transaction_id": tx.id}

    async def publish(self, app):
        """Publish new events to the subscribers."""
        logger.debug(f"DISPATCHER CALLED : {self.type}")
        while True:
            if self.type == "tx":
                event = await Dispatcher.get_queue_on_demand(app, "tx_source").get()
            elif self.type == "blk":
                event = await Dispatcher.get_queue_on_demand(app, "blk_source").get()
            str_buffer = []

            if event == POISON_PILL:
                return
            logger.debug(f"DISPATCHER ELEMENT : {event}")
            if isinstance(event, str):
                str_buffer.append(event)
            elif event.type == EventTypes.BLOCK_VALID:
                if self.type == "tx":
                    str_buffer = map(json.dumps, self.eventify_block(event.data))
                elif self.type == "blk":
                    str_buffer = [json.dumps(self.simplified_block(event.data))]
                else:
                    return

            for str_item in str_buffer:
                for _, websocket in self.subscribers.items():
                    await websocket.send_str(str_item)
