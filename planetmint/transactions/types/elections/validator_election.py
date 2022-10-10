# Copyright © 2020 Interplanetary Database Association e.V.,
# Planetmint and IPDB software contributors.
# SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
# Code is Apache-2.0 and docs are CC-BY-4.0

from planetmint.transactions.types.elections.election import Election
from planetmint.transactions.common.schema import TX_SCHEMA_VALIDATOR_ELECTION
from planetmint.transactions.common.transaction import VALIDATOR_ELECTION

from .validator_utils import new_validator_set, encode_validator, validate_asset_public_key


class ValidatorElection(Election):

    OPERATION = VALIDATOR_ELECTION
    ALLOWED_OPERATIONS = (OPERATION,)
    TX_SCHEMA_CUSTOM = TX_SCHEMA_VALIDATOR_ELECTION

    @classmethod
    def validate_schema(cls, tx):
        super(ValidatorElection, cls).validate_schema(tx)
        validate_asset_public_key(tx["asset"]["data"]["public_key"])

    def on_approval(self, planet, new_height): # TODO: move somewhere else
        validator_updates = [self.asset["data"]]
        curr_validator_set = planet.get_validators(new_height)
        updated_validator_set = new_validator_set(curr_validator_set, validator_updates)

        updated_validator_set = [v for v in updated_validator_set if v["voting_power"] > 0]

        # TODO change to `new_height + 2` when upgrading to Tendermint 0.24.0.
        planet.store_validator_set(new_height + 1, updated_validator_set)
        return encode_validator(self.asset["data"])
