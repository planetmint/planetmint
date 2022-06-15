# Copyright © 2020 Interplanetary Database Association e.V.,
# Planetmint and IPDB software contributors.
# SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
# Code is Apache-2.0 and docs are CC-BY-4.0

import logging
import setproctitle

import planetmint
from planetmint.lib import Planetmint
from planetmint.core import App
from planetmint.parallel_validation import ParallelValidationApp
from planetmint.web import server, websocket_server
from planetmint.events import Exchange, EventTypes
from planetmint.utils import Process


logger = logging.getLogger(__name__)

BANNER = """
****************************************************************************
*                                                                          *
*                             Planetmint 2.2.2                             *
*   codename "jumping sloth"                                               *
*   Initialization complete. Planetmint Server is ready and waiting.       *
*                                                                          *
*   You can send HTTP requests via the HTTP API documented in the          *
*   Planetmint Server docs at:                                             *
*    https://planetmint.com/http-api                                       *
*                                                                          *
*   Listening to client connections on: {:<15}                    *
*                                                                          *
****************************************************************************
"""


def start(args):
    # Exchange object for event stream api
    logger.info('Starting Planetmint')
    exchange = Exchange()
    # start the web api
    app_server = server.create_server(
        settings=planetmint.config['server'],
        log_config=planetmint.config['log'],
        planetmint_factory=Planetmint)
    p_webapi = Process(name='planetmint_webapi', target=app_server.run, daemon=False)
    p_webapi.start()

    logger.info(BANNER.format(planetmint.config['server']['bind']))

    # start websocket server
    p_websocket_server = Process(name='planetmint_ws',
                                 target=websocket_server.start,
                                 daemon=True,
                                 args=(exchange.get_subscriber_queue(EventTypes.BLOCK_VALID),))
    p_websocket_server.start()

    p_exchange = Process(name='planetmint_exchange', target=exchange.run, daemon=True)
    p_exchange.start()

    # We need to import this after spawning the web server
    # because import ABCIServer will monkeypatch all sockets
    # for gevent.
    from abci.server import ABCIServer

    setproctitle.setproctitle('planetmint')

    # Start the ABCIServer
    # abci = ABCI(TmVersion(planetmint.config['tendermint']['version']))
    if args.experimental_parallel_validation:
        app = ABCIServer(
            app=ParallelValidationApp(
                events_queue=exchange.get_publisher_queue(),
            )
        )
    else:
        app = ABCIServer(
            app=App(
                events_queue=exchange.get_publisher_queue(),
            )
        )
    app.run()


if __name__ == '__main__':
    start()
