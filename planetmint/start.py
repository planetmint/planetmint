# Copyright © 2020 Interplanetary Database Association e.V.,
# Planetmint and IPDB software contributors.
# SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
# Code is Apache-2.0 and docs are CC-BY-4.0

import logging
import setproctitle

from planetmint.config import Config
from planetmint.application.validator import Validator
from planetmint.abci.application_logic import ApplicationLogic
from planetmint.abci.parallel_validation import ParallelValidationApp
from planetmint.web import server, websocket_server
from planetmint.ipc.events import EventTypes
from planetmint.ipc.exchange import Exchange
from planetmint.utils import Process
from planetmint.version import __version__

logger = logging.getLogger(__name__)

BANNER = """
****************************************************************************
*                                                                          *
*                             Planetmint {}                     *
*   codename "jumping sloth"                                               *
*   Initialization complete. Planetmint Server is ready and waiting.       *
*                                                                          *
*   You can send HTTP requests via the HTTP API documented in the          *
*   Planetmint Server docs at:                                             *
*    https://planetmint.io/http-api                                       *
*                                                                          *
*   Listening to client connections on: {:<15}                    *
*                                                                          *
****************************************************************************
"""


def start_web_api(args):
    app_server = server.create_server(
        settings=Config().get()["server"], log_config=Config().get()["log"], planetmint_factory=Validator
    )
    if args.web_api_only:
        app_server.run()
    else:
        p_webapi = Process(name="planetmint_webapi", target=app_server.run, daemon=True)
        p_webapi.start()


def start_abci_server(args):
    logger.info(BANNER.format(__version__, Config().get()["server"]["bind"]))
    exchange = Exchange()

    # start websocket server
    p_websocket_server = Process(
        name="planetmint_ws",
        target=websocket_server.start,
        daemon=True,
        args=(exchange.get_subscriber_queue(EventTypes.BLOCK_VALID),),
    )
    p_websocket_server.start()

    p_exchange = Process(name="planetmint_exchange", target=exchange.run, daemon=True)
    p_exchange.start()

    # We need to import this after spawning the web server
    # because import ABCIServer will monkeypatch all sockets
    # for gevent.
    from abci.server import ABCIServer

    setproctitle.setproctitle("planetmint")

    abci_server_app = None

    publisher_queue = exchange.get_publisher_queue()
    if args.experimental_parallel_validation:
        abci_server_app = ParallelValidationApp(events_queue=publisher_queue)
    else:
        abci_server_app = ApplicationLogic(events_queue=publisher_queue)

    app = ABCIServer(abci_server_app)
    app.run()


def start(args):
    logger.info("Starting Planetmint")

    if args.web_api_only:
        start_web_api(args)
    elif args.abci_only:
        start_abci_server(args)
    else:
        start_web_api(args)
        start_abci_server(args)


if __name__ == "__main__":
    start()
