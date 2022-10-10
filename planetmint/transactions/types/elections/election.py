# Copyright © 2020 Interplanetary Database Association e.V.,
# Planetmint and IPDB software contributors.
# SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
# Code is Apache-2.0 and docs are CC-BY-4.0

from uuid import uuid4
from typing import Optional

from planetmint.transactions.common.transaction import Transaction
from planetmint.transactions.common.schema import _validate_schema, TX_SCHEMA_COMMON

class Election(Transaction):
    """Represents election transactions.

    To implement a custom election, create a class deriving from this one
    with OPERATION set to the election operation, ALLOWED_OPERATIONS
    set to (OPERATION,), CREATE set to OPERATION.
    """

    OPERATION: Optional[str] = None
    # Custom validation schema
    TX_SCHEMA_CUSTOM = None
    # Election Statuses:
    ONGOING: str = "ongoing"
    CONCLUDED: str = "concluded"
    INCONCLUSIVE: str = "inconclusive"
    # Vote ratio to approve an election
    ELECTION_THRESHOLD = 2 / 3

    @classmethod
    def validate_election(self, tx_signers, recipients, asset, metadata):
        if not isinstance(tx_signers, list):
            raise TypeError("`tx_signers` must be a list instance")
        if not isinstance(recipients, list):
            raise TypeError("`recipients` must be a list instance")
        if len(tx_signers) == 0:
            raise ValueError("`tx_signers` list cannot be empty")
        if len(recipients) == 0:
            raise ValueError("`recipients` list cannot be empty")
        if not asset is None:
            if not isinstance(asset, dict):
                raise TypeError("`asset` must be a CID string or None")
        if not (metadata is None or isinstance(metadata, str)):
            # add check if metadata is ipld marshalled CID string
            raise TypeError("`metadata` must be a CID string or None")

        return True

    @classmethod
    def generate(cls, initiator, voters, election_data, metadata=None):
        # Break symmetry in case we need to call an election with the same properties twice
        uuid = uuid4()
        election_data["seed"] = str(uuid)

        Election.validate_election(initiator, voters, election_data, metadata)
        (inputs, outputs) = Transaction.complete_tx_i_o(initiator, voters)
        election = cls(cls.OPERATION, {"data": election_data}, inputs, outputs, metadata)
        cls.validate_schema(election.to_dict())
        return election

    @classmethod
    def validate_schema(cls, tx):
        """Validate the election transaction. Since `ELECTION` extends `CREATE` transaction, all the validations for
        `CREATE` transaction should be inherited
        """
        _validate_schema(TX_SCHEMA_COMMON, tx)
        if cls.TX_SCHEMA_CUSTOM:
            _validate_schema(cls.TX_SCHEMA_CUSTOM, tx)

    def on_approval(self, planet, new_height):
        """Override to update the database state according to the
        election rules. Consider the current database state to account for
        other concluded elections, if required.
        """
        raise NotImplementedError

    def on_rollback(self, planet, new_height):
        """Override to clean up the database artifacts possibly created
        in `on_approval`. Part of the `end_block`/`commit` crash recovery.
        """
        raise NotImplementedError
