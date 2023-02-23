from uuid import uuid4

import requests
from transactions.common.exceptions import ValidationError

from planetmint.abci.tendermint_utils import encode_transaction
from planetmint.lib import logger
from transactions.common.transaction_mode_types import (
    BROADCAST_TX_COMMIT,
    BROADCAST_TX_ASYNC,
    BROADCAST_TX_SYNC,
)
MODE_COMMIT = BROADCAST_TX_COMMIT
MODE_LIST = (BROADCAST_TX_ASYNC, BROADCAST_TX_SYNC, MODE_COMMIT)

class ABCI_RPC:
    @staticmethod
    def _process_post_response(mode_commit, response, mode):
        logger.debug(response)

        error = response.get("error")
        if error:
            status_code = 500
            message = error.get("message", "Internal Error")
            data = error.get("data", "")

            if "Tx already exists in cache" in data:
                status_code = 400

            return (status_code, message + " - " + data)

        result = response["result"]
        if mode == mode_commit:
            check_tx_code = result.get("check_tx", {}).get("code", 0)
            deliver_tx_code = result.get("deliver_tx", {}).get("code", 0)
            error_code = check_tx_code or deliver_tx_code
        else:
            error_code = result.get("code", 0)

        if error_code:
            return (500, "Transaction validation failed")

        return (202, "")


    def write_transaction(self, mode_list, endpoint, mode_commit, transaction, mode):
        # This method offers backward compatibility with the Web API.
        """Submit a valid transaction to the mempool."""
        response = self.post_transaction(mode_list, endpoint, transaction, mode)
        return ABCI_RPC._process_post_response(mode_commit, response.json(), mode)


    def post_transaction(self, mode_list, endpoint, transaction, mode):
        """Submit a valid transaction to the mempool."""
        if not mode or mode not in mode_list:
            raise ValidationError("Mode must be one of the following {}.".format(", ".join(mode_list)))

        tx_dict = transaction.tx_dict if transaction.tx_dict else transaction.to_dict()
        payload = {
            "method": mode,
            "jsonrpc": "2.0",
            "params": [encode_transaction(tx_dict)],
            "id": str(uuid4()),
        }
        # TODO: handle connection errors!
        return requests.post(endpoint, json=payload)