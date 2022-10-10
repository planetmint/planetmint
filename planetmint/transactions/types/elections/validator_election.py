# Copyright © 2020 Interplanetary Database Association e.V.,
# Planetmint and IPDB software contributors.
# SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
# Code is Apache-2.0 and docs are CC-BY-4.0

from planetmint.transactions.types.elections.election import Election
from planetmint.transactions.common.schema import TX_SCHEMA_VALIDATOR_ELECTION
from planetmint.transactions.common.transaction import VALIDATOR_ELECTION

from .validator_utils import validate_asset_public_key


class ValidatorElection(Election):

    OPERATION = VALIDATOR_ELECTION
    ALLOWED_OPERATIONS = (OPERATION,)
    TX_SCHEMA_CUSTOM = TX_SCHEMA_VALIDATOR_ELECTION

    @classmethod
    def validate_schema(cls, tx):
        super(ValidatorElection, cls).validate_schema(tx)
        validate_asset_public_key(tx["asset"]["data"]["public_key"])
