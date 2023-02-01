# Copyright © 2020 Interplanetary Database Association e.V.,
# Planetmint and IPDB software contributors.
# SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
# Code is Apache-2.0 and docs are CC-BY-4.0

"""Common classes and methods for API handlers
"""
import logging

from flask import jsonify, request
from planetmint.config import Config


logger = logging.getLogger(__name__)


def make_error(status_code, message=None, level: str = "debug"):
    if status_code == 404 and message is None:
        message = "Not found"

    response_content = {"status": status_code, "message": message}
    request_info = {"method": request.method, "path": request.path}
    request_info.update(response_content)

    if level == "error":
        logger.error("HTTP API error: %(status)s - %(method)s:%(path)s - %(message)s", request_info)
    else:
        logger.debug("HTTP API error: %(status)s - %(method)s:%(path)s - %(message)s", request_info)

    response = jsonify(response_content)
    response.status_code = status_code
    return response


def base_ws_uri():
    """Base websocket URL that is advertised to external clients.

    Useful when the websocket URL advertised to the clients needs to be
    customized (typically when running behind NAT, firewall, etc.)
    """

    config_wsserver = Config().get()["wsserver"]

    scheme = config_wsserver["advertised_scheme"]
    host = config_wsserver["advertised_host"]
    port = config_wsserver["advertised_port"]

    return "{}://{}:{}".format(scheme, host, port)
