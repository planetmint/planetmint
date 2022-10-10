# Copyright © 2020 Interplanetary Database Association e.V.,
# Planetmint and IPDB software contributors.
# SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
# Code is Apache-2.0 and docs are CC-BY-4.0

from planetmint.transactions.common.schema import TX_SCHEMA_CHAIN_MIGRATION_ELECTION
from planetmint.transactions.common.transaction import CHAIN_MIGRATION_ELECTION
from planetmint.transactions.types.elections.election import Election


class ChainMigrationElection(Election):

    OPERATION = CHAIN_MIGRATION_ELECTION
    # CREATE = OPERATION
    ALLOWED_OPERATIONS = (OPERATION,)
    TX_SCHEMA_CUSTOM = TX_SCHEMA_CHAIN_MIGRATION_ELECTION

    def on_approval(self, planet, *args, **kwargs): # TODO: move somewhere else
        planet.migrate_abci_chain()
