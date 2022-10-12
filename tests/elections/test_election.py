import pytest

from tests.utils import generate_election, generate_validators
from planetmint.lib import Block
from transactions.types.elections.election import Election
from transactions.types.elections.chain_migration_election import ChainMigrationElection
from transactions.types.elections.validator_election import ValidatorElection


@pytest.mark.bdb
def test_process_block_concludes_all_elections(b):
    validators = generate_validators([1] * 4)
    b.store_validator_set(1, [v["storage"] for v in validators])

    new_validator = generate_validators([1])[0]

    public_key = validators[0]["public_key"]
    private_key = validators[0]["private_key"]
    voter_keys = [v["private_key"] for v in validators]

    election, votes = generate_election(b, ChainMigrationElection, public_key, private_key, {}, voter_keys)

    txs = [election]
    total_votes = votes

    election, votes = generate_election(
        b, ValidatorElection, public_key, private_key, new_validator["election"], voter_keys
    )
    txs += [election]
    total_votes += votes

    b.store_abci_chain(1, "chain-X")
    b.process_block(1, txs)
    b.store_block(Block(height=1, transactions=[tx.id for tx in txs], app_hash="")._asdict())
    b.store_bulk_transactions(txs)

    b.process_block(2, total_votes)

    validators = b.get_validators()
    assert len(validators) == 5
    assert new_validator["storage"] in validators

    chain = b.get_latest_abci_chain()
    assert chain
    assert chain == {
        "height": 2,
        "is_synced": False,
        "chain_id": "chain-X-migrated-at-height-1",
    }

    for tx in txs:
        assert b.get_election(tx.id)["is_concluded"]


@pytest.mark.bdb
def test_process_block_approves_only_one_validator_update(b):
    validators = generate_validators([1] * 4)
    b.store_validator_set(1, [v["storage"] for v in validators])

    new_validator = generate_validators([1])[0]

    public_key = validators[0]["public_key"]
    private_key = validators[0]["private_key"]
    voter_keys = [v["private_key"] for v in validators]

    election, votes = generate_election(
        b, ValidatorElection, public_key, private_key, new_validator["election"], voter_keys
    )
    txs = [election]
    total_votes = votes

    another_validator = generate_validators([1])[0]

    election, votes = generate_election(
        b, ValidatorElection, public_key, private_key, another_validator["election"], voter_keys
    )
    txs += [election]
    total_votes += votes

    b.process_block(1, txs)
    b.store_block(Block(height=1, transactions=[tx.id for tx in txs], app_hash="")._asdict())
    b.store_bulk_transactions(txs)

    b.process_block(2, total_votes)

    validators = b.get_validators()
    assert len(validators) == 5
    assert new_validator["storage"] in validators
    assert another_validator["storage"] not in validators

    assert b.get_election(txs[0].id)["is_concluded"]
    assert not b.get_election(txs[1].id)["is_concluded"]


@pytest.mark.bdb
def test_process_block_approves_after_pending_validator_update(b):
    validators = generate_validators([1] * 4)
    b.store_validator_set(1, [v["storage"] for v in validators])

    new_validator = generate_validators([1])[0]

    public_key = validators[0]["public_key"]
    private_key = validators[0]["private_key"]
    voter_keys = [v["private_key"] for v in validators]

    election, votes = generate_election(
        b, ValidatorElection, public_key, private_key, new_validator["election"], voter_keys
    )
    txs = [election]
    total_votes = votes

    another_validator = generate_validators([1])[0]

    election, votes = generate_election(
        b, ValidatorElection, public_key, private_key, another_validator["election"], voter_keys
    )
    txs += [election]
    total_votes += votes

    election, votes = generate_election(b, ChainMigrationElection, public_key, private_key, {}, voter_keys)

    txs += [election]
    total_votes += votes

    b.store_abci_chain(1, "chain-X")
    b.process_block(1, txs)
    b.store_block(Block(height=1, transactions=[tx.id for tx in txs], app_hash="")._asdict())
    b.store_bulk_transactions(txs)

    b.process_block(2, total_votes)

    validators = b.get_validators()
    assert len(validators) == 5
    assert new_validator["storage"] in validators
    assert another_validator["storage"] not in validators

    assert b.get_election(txs[0].id)["is_concluded"]
    assert not b.get_election(txs[1].id)["is_concluded"]
    assert b.get_election(txs[2].id)["is_concluded"]

    assert b.get_latest_abci_chain() == {"height": 2, "chain_id": "chain-X-migrated-at-height-1", "is_synced": False}


@pytest.mark.bdb
def test_process_block_does_not_approve_after_validator_update(b):
    validators = generate_validators([1] * 4)
    b.store_validator_set(1, [v["storage"] for v in validators])

    new_validator = generate_validators([1])[0]

    public_key = validators[0]["public_key"]
    private_key = validators[0]["private_key"]
    voter_keys = [v["private_key"] for v in validators]

    election, votes = generate_election(
        b, ValidatorElection, public_key, private_key, new_validator["election"], voter_keys
    )
    txs = [election]
    total_votes = votes

    b.store_block(Block(height=1, transactions=[tx.id for tx in txs], app_hash="")._asdict())
    b.process_block(1, txs)
    b.store_bulk_transactions(txs)

    second_election, second_votes = generate_election(
        b, ChainMigrationElection, public_key, private_key, {}, voter_keys
    )

    b.process_block(2, total_votes + [second_election])

    b.store_block(Block(height=2, transactions=[v.id for v in total_votes + [second_election]], app_hash="")._asdict())

    b.store_abci_chain(1, "chain-X")
    b.process_block(3, second_votes)

    assert not b.get_election(second_election.id)["is_concluded"]
    assert b.get_latest_abci_chain() == {"height": 1, "chain_id": "chain-X", "is_synced": True}


@pytest.mark.bdb
def test_process_block_applies_only_one_migration(b):
    validators = generate_validators([1] * 4)
    b.store_validator_set(1, [v["storage"] for v in validators])

    public_key = validators[0]["public_key"]
    private_key = validators[0]["private_key"]
    voter_keys = [v["private_key"] for v in validators]

    election, votes = generate_election(b, ChainMigrationElection, public_key, private_key, {}, voter_keys)
    txs = [election]
    total_votes = votes

    election, votes = generate_election(b, ChainMigrationElection, public_key, private_key, {}, voter_keys)

    txs += [election]
    total_votes += votes

    b.store_abci_chain(1, "chain-X")
    b.process_block(1, txs)
    b.store_block(Block(height=1, transactions=[tx.id for tx in txs], app_hash="")._asdict())
    b.store_bulk_transactions(txs)

    b.process_block(1, total_votes)
    chain = b.get_latest_abci_chain()
    assert chain
    assert chain == {
        "height": 2,
        "is_synced": False,
        "chain_id": "chain-X-migrated-at-height-1",
    }

    assert b.get_election(txs[0].id)["is_concluded"]
    assert not b.get_election(txs[1].id)["is_concluded"]


def test_process_block_gracefully_handles_empty_block(b):
    b.process_block(1, [])
