# Copyright © 2020 Interplanetary Database Association e.V.,
# Planetmint and IPDB software contributors.
# SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
# Code is Apache-2.0 and docs are CC-BY-4.0

import pytest
import codecs

from planetmint.model.dataaccessor import DataAccessor
from planetmint.abci.rpc import MODE_LIST, MODE_COMMIT
from planetmint.abci.utils import public_key_to_base64

from transactions.types.elections.validator_election import ValidatorElection
from transactions.common.exceptions import AmountError
from transactions.common.crypto import generate_key_pair
from transactions.common.exceptions import ValidationError
from transactions.common.transaction_mode_types import BROADCAST_TX_COMMIT
from transactions.types.elections.vote import Vote
from transactions.types.elections.validator_utils import election_id_to_public_key

from tests.utils import generate_block, gen_vote

pytestmark = [pytest.mark.execute]


# helper
def get_valid_upsert_election(m, b, mock_get_validators, node_key, new_validator):
    m.setattr(DataAccessor, "get_validators", mock_get_validators)
    voters = b.get_recipients_list()
    valid_upsert_validator_election = ValidatorElection.generate(
        [node_key.public_key], voters, new_validator, None
    ).sign([node_key.private_key])

    b.models.store_bulk_transactions([valid_upsert_validator_election])
    return valid_upsert_validator_election


# helper
def get_voting_set(valid_upsert_validator_election, ed25519_node_keys):
    input0 = valid_upsert_validator_election.to_inputs()[0]
    votes = valid_upsert_validator_election.outputs[0].amount
    public_key0 = input0.owners_before[0]
    key0 = ed25519_node_keys[public_key0]
    return input0, votes, key0


@pytest.mark.bdb
def test_upsert_validator_valid_election_vote(
    monkeypatch, b, network_validators, new_validator, node_key, ed25519_node_keys
):
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
        valid_upsert_validator_election = get_valid_upsert_election(m, b, mock_get_validators, node_key, new_validator)
        input0, votes, key0 = get_voting_set(valid_upsert_validator_election, ed25519_node_keys)

        election_pub_key = election_id_to_public_key(valid_upsert_validator_election.id)

        vote = Vote.generate(
            [input0], [([election_pub_key], votes)], election_ids=[valid_upsert_validator_election.id]
        ).sign([key0.private_key])
        assert b.validate_transaction(vote)
        m.undo()


@pytest.mark.bdb
def test_upsert_validator_valid_non_election_vote(
    monkeypatch, b, network_validators, node_key, new_validator, ed25519_node_keys
):
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
        valid_upsert_validator_election = get_valid_upsert_election(m, b, mock_get_validators, node_key, new_validator)
        input0, votes, key0 = get_voting_set(valid_upsert_validator_election, ed25519_node_keys)

        election_pub_key = election_id_to_public_key(valid_upsert_validator_election.id)

        # Ensure that threshold conditions are now allowed
        with pytest.raises(ValidationError):
            Vote.generate(
                [input0],
                [([election_pub_key, key0.public_key], votes)],
                election_ids=[valid_upsert_validator_election.id],
            ).sign([key0.private_key])
        m.undo()


@pytest.mark.bdb
def test_upsert_validator_delegate_election_vote(
    monkeypatch, b, network_validators, node_key, new_validator, ed25519_node_keys
):
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
        valid_upsert_validator_election = get_valid_upsert_election(m, b, mock_get_validators, node_key, new_validator)
        alice = generate_key_pair()
        input0, votes, key0 = get_voting_set(valid_upsert_validator_election, ed25519_node_keys)

        delegate_vote = Vote.generate(
            [input0],
            [([alice.public_key], 3), ([key0.public_key], votes - 3)],
            election_ids=[valid_upsert_validator_election.id],
        ).sign([key0.private_key])

        assert b.validate_transaction(delegate_vote)

        b.models.store_bulk_transactions([delegate_vote])
        election_pub_key = election_id_to_public_key(valid_upsert_validator_election.id)

        alice_votes = delegate_vote.to_inputs()[0]
        alice_casted_vote = Vote.generate(
            [alice_votes], [([election_pub_key], 3)], election_ids=[valid_upsert_validator_election.id]
        ).sign([alice.private_key])
        assert b.validate_transaction(alice_casted_vote)

        key0_votes = delegate_vote.to_inputs()[1]
        key0_casted_vote = Vote.generate(
            [key0_votes], [([election_pub_key], votes - 3)], election_ids=[valid_upsert_validator_election.id]
        ).sign([key0.private_key])
        assert b.validate_transaction(key0_casted_vote)
        m.undo()


@pytest.mark.bdb
def test_upsert_validator_invalid_election_vote(
    monkeypatch, b, network_validators, node_key, new_validator, ed25519_node_keys
):
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
        valid_upsert_validator_election = get_valid_upsert_election(m, b, mock_get_validators, node_key, new_validator)
        input0, votes, key0 = get_voting_set(valid_upsert_validator_election, ed25519_node_keys)

        election_pub_key = election_id_to_public_key(valid_upsert_validator_election.id)

        vote = Vote.generate(
            [input0], [([election_pub_key], votes + 1)], election_ids=[valid_upsert_validator_election.id]
        ).sign([key0.private_key])

        with pytest.raises(AmountError):
            assert b.validate_transaction(vote)


@pytest.mark.bdb
def test_valid_election_votes_received(monkeypatch, b, network_validators, node_key, new_validator, ed25519_node_keys):
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
        valid_upsert_validator_election = get_valid_upsert_election(m, b, mock_get_validators, node_key, new_validator)
        alice = generate_key_pair()

        assert b.get_commited_votes(valid_upsert_validator_election) == 0
        input0, votes, key0 = get_voting_set(valid_upsert_validator_election, ed25519_node_keys)

        # delegate some votes to alice
        delegate_vote = Vote.generate(
            [input0],
            [([alice.public_key], 4), ([key0.public_key], votes - 4)],
            election_ids=[valid_upsert_validator_election.id],
        ).sign([key0.private_key])
        b.models.store_bulk_transactions([delegate_vote])
        assert b.get_commited_votes(valid_upsert_validator_election) == 0

        election_public_key = election_id_to_public_key(valid_upsert_validator_election.id)
        alice_votes = delegate_vote.to_inputs()[0]
        key0_votes = delegate_vote.to_inputs()[1]

        alice_casted_vote = Vote.generate(
            [alice_votes],
            [([election_public_key], 2), ([alice.public_key], 2)],
            election_ids=[valid_upsert_validator_election.id],
        ).sign([alice.private_key])

        assert b.validate_transaction(alice_casted_vote)
        b.models.store_bulk_transactions([alice_casted_vote])

        # Check if the delegated vote is count as valid vote
        assert b.get_commited_votes(valid_upsert_validator_election) == 2

        key0_casted_vote = Vote.generate(
            [key0_votes], [([election_public_key], votes - 4)], election_ids=[valid_upsert_validator_election.id]
        ).sign([key0.private_key])

        assert b.validate_transaction(key0_casted_vote)
        b.models.store_bulk_transactions([key0_casted_vote])
        assert b.get_commited_votes(valid_upsert_validator_election) == votes - 2


@pytest.mark.bdb
def test_valid_election_conclude(monkeypatch, b, network_validators, node_key, new_validator, ed25519_node_keys):
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
        valid_upsert_validator_election = ValidatorElection.generate(
            [node_key.public_key], voters, new_validator, None
        ).sign([node_key.private_key])

        # Node 0: cast vote
        tx_vote0 = gen_vote(valid_upsert_validator_election, 0, ed25519_node_keys)

        # check if the vote is valid even before the election doesn't exist
        with pytest.raises(ValidationError):
            assert b.validate_transaction(tx_vote0)

        # store election
        b.models.store_bulk_transactions([valid_upsert_validator_election])
        # cannot conclude election as not votes exist
        assert not b.has_election_concluded(valid_upsert_validator_election)

        # validate vote
        assert b.validate_transaction(tx_vote0)
        assert not b.has_election_concluded(valid_upsert_validator_election, [tx_vote0])

        b.models.store_bulk_transactions([tx_vote0])
        assert not b.has_election_concluded(valid_upsert_validator_election)

        # Node 1: cast vote
        tx_vote1 = gen_vote(valid_upsert_validator_election, 1, ed25519_node_keys)

        # Node 2: cast vote
        tx_vote2 = gen_vote(valid_upsert_validator_election, 2, ed25519_node_keys)

        # Node 3: cast vote
        tx_vote3 = gen_vote(valid_upsert_validator_election, 3, ed25519_node_keys)

        assert b.validate_transaction(tx_vote1)
        assert not b.has_election_concluded(valid_upsert_validator_election, [tx_vote1])

        # 2/3 is achieved in the same block so the election can be.has_concludedd
        assert b.has_election_concluded(valid_upsert_validator_election, [tx_vote1, tx_vote2])

        b.models.store_bulk_transactions([tx_vote1])
        assert not b.has_election_concluded(valid_upsert_validator_election)

        assert b.validate_transaction(tx_vote2)
        assert b.validate_transaction(tx_vote3)

        # conclusion can be triggered my different votes in the same block
        assert b.has_election_concluded(valid_upsert_validator_election, [tx_vote2])
        assert b.has_election_concluded(valid_upsert_validator_election, [tx_vote2, tx_vote3])

        b.models.store_bulk_transactions([tx_vote2])

        # Once the blockchain records >2/3 of the votes the election is assumed to be.has_concludedd
        # so any invocation of `.has_concluded` for that election should return False
        assert not b.has_election_concluded(valid_upsert_validator_election)

        # Vote is still valid but the election cannot be.has_concluded as it it assumed that it has
        # been.has_concludedd before
        assert b.validate_transaction(tx_vote3)
        assert not b.has_election_concluded(valid_upsert_validator_election, [tx_vote3])


@pytest.mark.abci
def test_upsert_validator(b, node_key, node_keys, ed25519_node_keys, test_abci_rpc):
    if b.models.get_latest_block()["height"] == 0:
        generate_block(b, test_abci_rpc)

    (node_pub, _) = list(node_keys.items())[0]

    validators = [{"public_key": {"type": "ed25519-base64", "value": node_pub}, "voting_power": 10}]

    latest_block = b.models.get_latest_block()
    # reset the validator set
    b.models.store_validator_set(latest_block["height"], validators)
    generate_block(b, test_abci_rpc)

    power = 1
    public_key = "9B3119650DF82B9A5D8A12E38953EA47475C09F0C48A4E6A0ECE182944B24403"
    public_key64 = public_key_to_base64(public_key)
    new_validator = [
        {
            "data": {
                "public_key": {"value": public_key, "type": "ed25519-base16"},
                "node_id": "some_node_id",
                "power": power,
            }
        }
    ]

    voters = b.get_recipients_list()
    election = ValidatorElection.generate([node_key.public_key], voters, new_validator, None).sign(
        [node_key.private_key]
    )
    code, message = test_abci_rpc.write_transaction(
        MODE_LIST, test_abci_rpc.tendermint_rpc_endpoint, MODE_COMMIT, election, BROADCAST_TX_COMMIT
    )
    assert code == 202
    assert b.models.get_transaction(election.id)

    tx_vote = gen_vote(election, 0, ed25519_node_keys)
    assert b.validate_transaction(tx_vote)
    code, message = test_abci_rpc.write_transaction(
        MODE_LIST, test_abci_rpc.tendermint_rpc_endpoint, MODE_COMMIT, tx_vote, BROADCAST_TX_COMMIT
    )
    assert code == 202

    resp = b.models.get_validators()
    validator_pub_keys = []
    for v in resp:
        validator_pub_keys.append(v["public_key"]["value"])

    assert public_key64 in validator_pub_keys
    new_validator_set = b.models.get_validators()
    validator_pub_keys = []
    for v in new_validator_set:
        validator_pub_keys.append(v["public_key"]["value"])

    assert public_key64 in validator_pub_keys


@pytest.mark.bdb
def test_get_validator_update(b, node_keys, node_key, ed25519_node_keys):
    reset_validator_set(b, node_keys, 1)

    power = 1
    public_key = "9B3119650DF82B9A5D8A12E38953EA47475C09F0C48A4E6A0ECE182944B24403"
    public_key64 = public_key_to_base64(public_key)
    new_validator = [
        {
            "data": {
                "public_key": {"value": public_key, "type": "ed25519-base16"},
                "node_id": "some_node_id",
                "power": power,
            }
        }
    ]
    voters = b.get_recipients_list()
    election = ValidatorElection.generate([node_key.public_key], voters, new_validator).sign([node_key.private_key])
    # store election
    b.models.store_bulk_transactions([election])

    tx_vote0 = gen_vote(election, 0, ed25519_node_keys)
    tx_vote1 = gen_vote(election, 1, ed25519_node_keys)
    tx_vote2 = gen_vote(election, 2, ed25519_node_keys)

    assert not b.has_election_concluded(election, [tx_vote0])
    assert not b.has_election_concluded(election, [tx_vote0, tx_vote1])
    assert b.has_election_concluded(election, [tx_vote0, tx_vote1, tx_vote2])

    assert b.process_block(4, [tx_vote0]) == []
    assert b.process_block(4, [tx_vote0, tx_vote1]) == []

    update = b.process_block(4, [tx_vote0, tx_vote1, tx_vote2])
    assert len(update) == 1
    update_public_key = codecs.encode(update[0].pub_key.ed25519, "base64").decode().rstrip("\n")
    assert update_public_key == public_key64

    # remove validator
    power = 0
    new_validator = [
        {
            "data": {
                "public_key": {"value": public_key, "type": "ed25519-base16"},
                "node_id": "some_node_id",
                "power": power,
            }
        }
    ]
    voters = b.get_recipients_list()
    election = ValidatorElection.generate([node_key.public_key], voters, new_validator).sign([node_key.private_key])
    # store election
    b.models.store_bulk_transactions([election])

    tx_vote0 = gen_vote(election, 0, ed25519_node_keys)
    tx_vote1 = gen_vote(election, 1, ed25519_node_keys)
    tx_vote2 = gen_vote(election, 2, ed25519_node_keys)

    b.models.store_bulk_transactions([tx_vote0, tx_vote1])

    update = b.process_block(9, [tx_vote2])
    assert len(update) == 1
    update_public_key = codecs.encode(update[0].pub_key.ed25519, "base64").decode().rstrip("\n")
    assert update_public_key == public_key64

    # assert that the public key is not a part of the current validator set
    for v in b.models.get_validators(10):
        assert not v["public_key"]["value"] == public_key64


# ============================================================================
# Helper functions
# ============================================================================


def reset_validator_set(b, node_keys, height):
    validators = []
    for node_pub, _ in node_keys.items():
        validators.append({"public_key": {"type": "ed25519-base64", "value": node_pub}, "voting_power": 10})
    b.models.store_validator_set(height, validators)
