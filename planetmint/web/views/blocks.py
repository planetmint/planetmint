# Copyright © 2020 Interplanetary Database Association e.V.,
# Planetmint and IPDB software contributors.
# SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
# Code is Apache-2.0 and docs are CC-BY-4.0

"""This module provides the blueprint for the blocks API endpoints.

For more information please refer to the documentation: http://planetmint.io/http-api
"""
from flask import current_app
from flask_restful import Resource, reqparse
from planetmint.web.views.base import make_error


class LatestBlock(Resource):
    def get(self):
        """API endpoint to get details about a block.

        Return:
            A JSON string containing the data about the block.
        """

        validator_class = current_app.config["validator_class_name"]

        with validator_class() as validator:
            block = validator.models.get_latest_block()

        if not block:
            return make_error(404)

        return block


class BlockApi(Resource):
    def get(self, block_id):
        """API endpoint to get details about a block.

        Args:
            block_id (str): the id of the block.

        Return:
            A JSON string containing the data about the block.
        """

        validator_class = current_app.config["validator_class_name"]

        with validator_class() as validator:
            block = validator.models.get_block(block_id=block_id)

        if not block:
            return make_error(404)

        return block


class BlockListApi(Resource):
    def get(self):
        """API endpoint to get the related blocks for a transaction.

        Return:
            A ``list`` of ``block_id``s that contain the given transaction. The
            list may be filtered when provided a status query parameter:
            "valid", "invalid", "undecided".
        """
        parser = reqparse.RequestParser()
        parser.add_argument("transaction_id", type=str, required=True)

        args = parser.parse_args(strict=True)
        tx_id = args["transaction_id"]

        validator_class = current_app.config["validator_class_name"]

        with validator_class() as validator:
            block = validator.models.get_block_containing_tx(tx_id)

        if not block:
            return make_error(404, "Block containing transaction with id: {} not found.".format(tx_id))

        return block
