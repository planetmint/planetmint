# Copyright © 2020 Interplanetary Database Association e.V.,
# Planetmint and IPDB software contributors.
# SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
# Code is Apache-2.0 and docs are CC-BY-4.0


import json

from planetmint.ipc.events import EventTypes
from planetmint.ipc.events import POISON_PILL


class Dispatcher:
    """Dispatch events to websockets.

    This class implements a simple publish/subscribe pattern.
    """

    def __init__(self, event_source, type="tx"):
        """Create a new instance.

        Args:
            event_source: a source of events. Elements in the queue
            should be strings.
        """

        self.event_source = event_source
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
    def eventify_block(block):
        for tx in block["transactions"]:
            if tx.assets:
                asset_ids = [asset.get("id", tx.id) for asset in tx.assets]
            else:
                asset_ids = [tx.id]
            yield {"height": block["height"], "asset_ids": asset_ids, "transaction_id": tx.id}

    async def publish(self):
        """Publish new events to the subscribers."""

        while True:
            event = await self.event_source.get()
            str_buffer = []

            if event == POISON_PILL:
                return

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
