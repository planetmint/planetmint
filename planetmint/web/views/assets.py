# Copyright © 2020 Interplanetary Database Association e.V.,
# Planetmint and IPDB software contributors.
# SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
# Code is Apache-2.0 and docs are CC-BY-4.0

"""This module provides the blueprint for some basic API endpoints.

For more information please refer to the documentation: http://planetmint.io/http-api
"""
import logging

from flask_restful import Resource, reqparse
from flask import current_app
from planetmint.backend.exceptions import OperationError
from planetmint.web.views.base import make_error

logger = logging.getLogger(__name__)


class AssetListApi(Resource):
    def get(self, cid: str):
        parser = reqparse.RequestParser()
        parser.add_argument("limit", type=int)
        args = parser.parse_args()

        if not args["limit"]:
            del args["limit"]

        validator_class = current_app.config["validator_class_name"]

        with validator_class() as validator:
            assets = validator.models.get_assets_by_cid(cid, **args)

        try:
            # This only works with MongoDB as the backend
            return assets
        except OperationError as e:
            return make_error(400, "({}): {}".format(type(e).__name__, e))
