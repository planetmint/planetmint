import json

from planetmint.transactions.common.schema import TX_SCHEMA_CHAIN_MIGRATION_ELECTION
from planetmint.transactions.common.transaction import CHAIN_MIGRATION_ELECTION
from planetmint.transactions.types.elections.election import Election


class ChainMigrationElection(Election):

    OPERATION = CHAIN_MIGRATION_ELECTION
    # CREATE = OPERATION
    ALLOWED_OPERATIONS = (OPERATION,)
    TX_SCHEMA_CUSTOM = TX_SCHEMA_CHAIN_MIGRATION_ELECTION

    def has_concluded(self, planetmint, *args, **kwargs): # TODO: move somewhere else
        chain = planetmint.get_latest_abci_chain()
        if chain is not None and not chain["is_synced"]:
            # do not conclude the migration election if
            # there is another migration in progress
            return False

        return super().has_concluded(planetmint, *args, **kwargs)

    def on_approval(self, planet, *args, **kwargs): # TODO: move somewhere else
        planet.migrate_abci_chain()

    def on_rollback(self, planet, new_height): # TODO: move somewhere else
        planet.delete_abci_chain(new_height)
