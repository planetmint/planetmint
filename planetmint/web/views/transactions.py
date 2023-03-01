# Copyright © 2020 Interplanetary Database Association e.V.,
# Planetmint and IPDB software contributors.
# SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
# Code is Apache-2.0 and docs are CC-BY-4.0

"""This module provides the blueprint for some basic API endpoints.

For more information please refer to the documentation: http://planetmint.io/http-api
"""
import logging

from flask import current_app, request, jsonify
from flask_restful import Resource, reqparse
from transactions.common.transaction import Transaction
from transactions.common.transaction_mode_types import BROADCAST_TX_ASYNC
from transactions.common.exceptions import (
    SchemaValidationError,
    ValidationError,
)
from planetmint.abci.rpc import ABCI_RPC, MODE_COMMIT, MODE_LIST
from planetmint.web.views import parameters
from planetmint.web.views.base import make_error

logger = logging.getLogger(__name__)


class TransactionApi(Resource):
    def get(self, tx_id):
        """API endpoint to get details about a transaction.

        Args:
            tx_id (str): the id of the transaction.

        Return:
            A JSON string containing the data about the transaction.
        """
        validator_class = current_app.config["validator_class_name"]

        with validator_class() as validator:
            tx = validator.models.get_transaction(tx_id)

        if not tx:
            return make_error(404)

        return tx.to_dict()


class TransactionListApi(Resource):
    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument("operation", type=parameters.valid_operation)
        parser.add_argument("asset_ids", type=parameters.valid_txid_list, required=True)
        parser.add_argument("last_tx", type=parameters.valid_bool, required=False)
        args = parser.parse_args()
        with current_app.config["validator_class_name"]() as validator:
            txs = validator.models.get_transactions_filtered(**args)

        return [tx.to_dict() for tx in txs]

    def post(self):
        """API endpoint to push transactions to the Federation.

        Return:
            A ``dict`` containing the data about the transaction.
        """
        parser = reqparse.RequestParser()
        parser.add_argument("mode", type=parameters.valid_mode, default=BROADCAST_TX_ASYNC)
        args = parser.parse_args()
        mode = str(args["mode"])

        validator_class = current_app.config["validator_class_name"]

        # `force` will try to format the body of the POST request even if the
        # `content-type` header is not set to `application/json`
        tx = request.get_json(force=True)
        try:
            tx_obj = Transaction.from_dict(tx, False)
        except SchemaValidationError as e:
            return make_error(
                400,
                message="Invalid transaction schema: {}".format(e.__cause__.message),
            )
        except KeyError as e:
            return make_error(400, "Invalid transaction ({}): {}".format(type(e).__name__, e))
        except ValidationError as e:
            return make_error(400, "Invalid transaction ({}): {}".format(type(e).__name__, e))
        except Exception as e:
            return make_error(500, "Invalid transaction ({}): {} - {}".format(type(e).__name__, e, tx), level="error")

        with validator_class() as validator:
            try:
                validator.validate_transaction(tx_obj)
            except ValidationError as e:
                return make_error(400, "Invalid transaction ({}): {}".format(type(e).__name__, e))
            except Exception as e:
                return make_error(
                    500, "Invalid transaction ({}): {} : {}".format(type(e).__name__, e, tx), level="error"
                )
            else:
                if tx_obj.version != Transaction.VERSION:
                    return make_error(
                        401,
                        "Invalid transaction version: The transaction is valid, \
                            but this node only accepts transaction with higher \
                            schema version number.",
                    )
                status_code, message = ABCI_RPC().write_transaction(
                    MODE_LIST, ABCI_RPC().tendermint_rpc_endpoint, MODE_COMMIT, tx_obj, mode
                )

        if status_code == 202:
            response = jsonify(tx)
            response.status_code = 202
            return response
        else:
            return make_error(status_code, message)
