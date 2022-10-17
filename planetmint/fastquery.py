# Copyright © 2020 Interplanetary Database Association e.V.,
# Planetmint and IPDB software contributors.
# SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
# Code is Apache-2.0 and docs are CC-BY-4.0

from planetmint.utils import condition_details_has_owner
from planetmint.backend import query
from transactions.common.transaction import TransactionLink


class FastQuery:
    """Database queries that join on block results from a single node."""

    def __init__(self, connection):
        self.connection = connection

    def get_outputs_by_public_key(self, public_key):
        """Get outputs for a public key"""
        txs = list(query.get_owned_ids(self.connection, public_key))
        return [
            TransactionLink(tx["id"], index)
            for tx in txs
            for index, output in enumerate(tx["outputs"])
            if condition_details_has_owner(output["condition"]["details"], public_key)
        ]

    def filter_spent_outputs(self, outputs):
        """Remove outputs that have been spent

        Args:
            outputs: list of TransactionLink
        """
        links = [o.to_dict() for o in outputs]
        txs = list(query.get_spending_transactions(self.connection, links))
        spends = {TransactionLink.from_dict(input_["fulfills"]) for tx in txs for input_ in tx["inputs"]}
        return [ff for ff in outputs if ff not in spends]

    def filter_unspent_outputs(self, outputs):
        """Remove outputs that have not been spent

        Args:
            outputs: list of TransactionLink
        """
        links = [o.to_dict() for o in outputs]
        txs = list(query.get_spending_transactions(self.connection, links))
        spends = {TransactionLink.from_dict(input_["fulfills"]) for tx in txs for input_ in tx["inputs"]}
        return [ff for ff in outputs if ff in spends]
