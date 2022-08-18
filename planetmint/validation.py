# Copyright © 2020 Interplanetary Database Association e.V.,
# Planetmint and IPDB software contributors.
# SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
# Code is Apache-2.0 and docs are CC-BY-4.0


class BaseValidationRules:
    """Base validation rules for Planetmint.

    A validation plugin must expose a class inheriting from this one via an entry_point.

    All methods listed below must be implemented.
    """

    @staticmethod
    def validate_transaction(planetmint, transaction):
        """See :meth:`planetmint.models.Transaction.validate`
        for documentation.
        """
        return transaction.validate(planetmint)

    @staticmethod
    def validate_block(planetmint, block):
        """See :meth:`planetmint.models.Block.validate` for documentation."""
        return block.validate(planetmint)
