import json

from planetmint.transactions.common.schema import TX_SCHEMA_CHAIN_MIGRATION_ELECTION
from planetmint.transactions.common.transaction import CHAIN_MIGRATION_ELECTION
from planetmint.transactions.types.elections.election import Election


class ChainMigrationElection(Election):

    OPERATION = CHAIN_MIGRATION_ELECTION
    # CREATE = OPERATION
    ALLOWED_OPERATIONS = (OPERATION,)
    TX_SCHEMA_CUSTOM = TX_SCHEMA_CHAIN_MIGRATION_ELECTION

    def has_concluded(self, planetmint, *args, **kwargs):
        chain = planetmint.get_latest_abci_chain()
        if chain is not None and not chain["is_synced"]:
            # do not conclude the migration election if
            # there is another migration in progress
            return False

        return super().has_concluded(planetmint, *args, **kwargs)

    def on_approval(self, planet, *args, **kwargs):
        planet.migrate_abci_chain()

    def show_election(self, planet):
        output = super().show_election(planet)
        chain = planet.get_latest_abci_chain()
        if chain is None or chain["is_synced"]:
            return output

        output += f'\nchain_id={chain["chain_id"]}'
        block = planet.get_latest_block()
        output += f'\napp_hash={block["app_hash"]}'
        validators = [
            {
                "pub_key": {
                    "type": "tendermint/PubKeyEd25519",
                    "value": k,
                },
                "power": v,
            }
            for k, v in self.get_validators(planet).items()
        ]
        output += f"\nvalidators={json.dumps(validators, indent=4)}"
        return output

    def on_rollback(self, planet, new_height):
        planet.delete_abci_chain(new_height)
