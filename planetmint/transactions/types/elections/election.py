# Copyright © 2020 Interplanetary Database Association e.V.,
# Planetmint and IPDB software contributors.
# SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
# Code is Apache-2.0 and docs are CC-BY-4.0
from collections import OrderedDict

from uuid import uuid4
from typing import Optional

from planetmint.transactions.types.elections.vote import Vote
from planetmint.transactions.common.transaction import Transaction
from planetmint.transactions.common.schema import _validate_schema, TX_SCHEMA_COMMON

from .validator_utils import election_id_to_public_key

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

    def has_concluded(self, planet, current_votes=[]): # TODO: move somewhere else
        """Check if the election can be concluded or not.

        * Elections can only be concluded if the validator set has not changed
          since the election was initiated.
        * Elections can be concluded only if the current votes form a supermajority.

        Custom elections may override this function and introduce additional checks.
        """
        if planet.has_validator_set_changed(self):
            return False

        election_pk = election_id_to_public_key(self.id)
        votes_committed = planet.get_commited_votes(self, election_pk)
        votes_current = planet.count_votes(election_pk, current_votes)

        total_votes = sum(output.amount for output in self.outputs)
        if (votes_committed < (2 / 3) * total_votes) and (votes_committed + votes_current >= (2 / 3) * total_votes):
            return True

        return False

    @classmethod
    def rollback(cls, planet, new_height, txn_ids): # TODO: move somewhere else
        """Looks for election and vote transactions inside the block and
        cleans up the database artifacts possibly created in `process_blocks`.

        Part of the `end_block`/`commit` crash recovery.
        """

        # delete election records for elections initiated at this height and
        # elections concluded at this height
        planet.delete_elections(new_height)

        txns = [planet.get_transaction(tx_id) for tx_id in txn_ids]

        elections = planet._get_votes(txns)
        for election_id in elections:
            election = planet.get_transaction(election_id)
            election.on_rollback(planet, new_height)

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
