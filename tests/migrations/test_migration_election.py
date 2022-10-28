from transactions.types.elections.chain_migration_election import ChainMigrationElection


def test_valid_migration_election(b_mock, node_key):
    voters = b_mock.get_recipients_list()
    election = ChainMigrationElection.generate([node_key.public_key], voters, [{"data": {}}], None).sign(
        [node_key.private_key]
    )
    assert b_mock.validate_election(election)
