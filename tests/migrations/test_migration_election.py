import pytest
from transactions.types.elections.chain_migration_election import ChainMigrationElection


@pytest.mark.bdb
def test_valid_migration_election(monkeypatch, b, node_key, network_validators):
    def mock_get_validators(self, height):
        validators = []
        for public_key, power in network_validators.items():
            validators.append(
                {
                    "public_key": {"type": "ed25519-base64", "value": public_key},
                    "voting_power": power,
                }
            )
        return validators

    with monkeypatch.context() as m:
        from planetmint.model.dataaccessor import DataAccessor

        m.setattr(DataAccessor, "get_validators", mock_get_validators)

        voters = b.get_recipients_list()
        election = ChainMigrationElection.generate([node_key.public_key], voters, [{"data": {}}], None).sign(
            [node_key.private_key]
        )
        assert b.validate_election(election)
        m.undo()
