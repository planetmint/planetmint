# Copyright © 2020 Interplanetary Database Association e.V.,
# Planetmint and IPDB software contributors.
# SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
# Code is Apache-2.0 and docs are CC-BY-4.0

"""API Index endpoint"""

import flask

from flask_restful import Resource
from planetmint.web.views.base import base_ws_uri
from planetmint import version
from planetmint.web.websocket_server import EVENTS_ENDPOINT, EVENTS_ENDPOINT_BLOCKS


class RootIndex(Resource):
    def get(self):
        docs_url = ["https://docs.planetmint.io/projects/server/en/v", version.__version__ + "/"]
        return flask.jsonify(
            {
                "api": {"v1": get_api_v1_info("/api/v1/")},
                "docs": "".join(docs_url),
                "software": "Planetmint",
                "version": version.__version__,
            }
        )


class ApiV1Index(Resource):
    def get(self):
        return flask.jsonify(get_api_v1_info("/"))


def get_api_v1_info(api_prefix):
    """Return a dict with all the information specific for the v1 of the
    api.
    """
    websocket_root_tx = base_ws_uri() + EVENTS_ENDPOINT
    websocket_root_block = base_ws_uri() + EVENTS_ENDPOINT_BLOCKS
    docs_url = [
        "https://docs.planetmint.io/projects/server/en/v",
        version.__version__,
        "/http-client-server-api.html",
    ]

    return {
        "docs": "".join(docs_url),
        "transactions": "{}transactions/".format(api_prefix),
        "blocks": "{}blocks/".format(api_prefix),
        "assets": "{}assets/".format(api_prefix),
        "outputs": "{}outputs/".format(api_prefix),
        "streams": websocket_root_tx,
        "streamedblocks": websocket_root_block,
        "metadata": "{}metadata/".format(api_prefix),
        "validators": "{}validators".format(api_prefix),
    }
