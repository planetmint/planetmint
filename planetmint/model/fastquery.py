# Copyright © 2020 Interplanetary Database Association e.V.,
# Planetmint and IPDB software contributors.
# SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
# Code is Apache-2.0 and docs are CC-BY-4.0

from planetmint.backend import query
from transactions.common.transaction import TransactionLink

from planetmint.backend.models.output import ConditionDetails


class FastQuery:
    """Database queries that join on block results from a single node."""

    def __init__(self, connection):
        self.connection = connection

    def get_outputs_by_public_key(self, public_key):
        """Get outputs for a public key"""
        txs = query.get_owned_ids(self.connection, public_key)
        return [
            TransactionLink(tx.id, index)
            for tx in txs
            for index, output in enumerate(tx.outputs)
            if condition_details_has_owner(output.condition.details, public_key)
        ]

    def filter_spent_outputs(self, outputs):
        """Remove outputs that have been spent

        Args:
            outputs: list of TransactionLink
        """
        links = [o.to_dict() for o in outputs]
        txs = query.get_spending_transactions(self.connection, links)
        spends = {TransactionLink.from_dict(input.fulfills.to_dict()) for tx in txs for input in tx.inputs}
        return [ff for ff in outputs if ff not in spends]

    def filter_unspent_outputs(self, outputs):
        """Remove outputs that have not been spent

        Args:
            outputs: list of TransactionLink
        """
        links = [o.to_dict() for o in outputs]
        txs = query.get_spending_transactions(self.connection, links)
        spends = {TransactionLink.from_dict(input.fulfills.to_dict()) for tx in txs for input in tx.inputs}
        return [ff for ff in outputs if ff in spends]


# TODO: Rename this function, it's handling fulfillments not conditions
def condition_details_has_owner(condition_details, owner):
    """Check if the public_key of owner is in the condition details
    as an Ed25519Fulfillment.public_key

    Args:
        condition_details (dict): dict with condition details
        owner (str): base58 public key of owner

    Returns:
        bool: True if the public key is found in the condition details, False otherwise

    """
    if isinstance(condition_details, ConditionDetails) and condition_details.sub_conditions is not None:
        result = condition_details_has_owner(condition_details.sub_conditions, owner)
        if result:
            return True
    elif isinstance(condition_details, list):
        for subcondition in condition_details:
            result = condition_details_has_owner(subcondition, owner)
            if result:
                return True
    else:
        if condition_details.public_key is not None and owner == condition_details.public_key:
            return True
    return False
