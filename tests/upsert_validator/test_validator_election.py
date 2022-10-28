# Copyright © 2020 Interplanetary Database Association e.V.,
# Planetmint and IPDB software contributors.
# SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
# Code is Apache-2.0 and docs are CC-BY-4.0

import pytest

from argparse import Namespace
from unittest.mock import patch
from planetmint.tendermint_utils import public_key_to_base64
from transactions.types.elections.validator_election import ValidatorElection
from transactions.common.exceptions import (
    DuplicateTransaction,
    UnequalValidatorSet,
    InvalidProposer,
    MultipleInputsError,
    InvalidPowerChange,
)

pytestmark = pytest.mark.bdb


def test_upsert_validator_valid_election(b_mock, new_validator, node_key):
    voters = b_mock.get_recipients_list()
    election = ValidatorElection.generate([node_key.public_key], voters, new_validator, None).sign(
        [node_key.private_key]
    )
    assert b_mock.validate_election(election)


def test_upsert_validator_invalid_election_public_key(b_mock, new_validator, node_key):
    from transactions.common.exceptions import InvalidPublicKey

    for iv in ["ed25519-base32", "ed25519-base64"]:
        new_validator[0]["data"]["public_key"]["type"] = iv
        voters = b_mock.get_recipients_list()

        with pytest.raises(InvalidPublicKey):
            ValidatorElection.generate([node_key.public_key], voters, new_validator, None).sign([node_key.private_key])


def test_upsert_validator_invalid_power_election(b_mock, new_validator, node_key):
    voters = b_mock.get_recipients_list()
    new_validator[0]["data"]["power"] = 30

    election = ValidatorElection.generate([node_key.public_key], voters, new_validator, None).sign(
        [node_key.private_key]
    )
    with pytest.raises(InvalidPowerChange):
        b_mock.validate_election(election)


def test_upsert_validator_invalid_proposed_election(b_mock, new_validator, node_key):
    from transactions.common.crypto import generate_key_pair

    alice = generate_key_pair()
    voters = b_mock.get_recipients_list()
    election = ValidatorElection.generate([alice.public_key], voters, new_validator, None).sign([alice.private_key])
    with pytest.raises(InvalidProposer):
        b_mock.validate_election(election)


def test_upsert_validator_invalid_inputs_election(b_mock, new_validator, node_key):
    from transactions.common.crypto import generate_key_pair

    alice = generate_key_pair()
    voters = b_mock.get_recipients_list()
    election = ValidatorElection.generate([node_key.public_key, alice.public_key], voters, new_validator, None).sign(
        [node_key.private_key, alice.private_key]
    )
    with pytest.raises(MultipleInputsError):
        b_mock.validate_election(election)


@patch("transactions.types.elections.election.uuid4", lambda: "mock_uuid4")
def test_upsert_validator_invalid_election(b_mock, new_validator, node_key, fixed_seed_election):
    voters = b_mock.get_recipients_list()
    duplicate_election = ValidatorElection.generate([node_key.public_key], voters, new_validator, None).sign(
        [node_key.private_key]
    )

    with pytest.raises(DuplicateTransaction):
        b_mock.validate_election(fixed_seed_election, [duplicate_election])

    b_mock.store_bulk_transactions([fixed_seed_election])

    with pytest.raises(DuplicateTransaction):
        b_mock.validate_election(duplicate_election)

    # Try creating an election with incomplete voter set
    invalid_election = ValidatorElection.generate([node_key.public_key], voters[1:], new_validator, None).sign(
        [node_key.private_key]
    )

    with pytest.raises(UnequalValidatorSet):
        b_mock.validate_election(invalid_election)

    recipients = b_mock.get_recipients_list()
    altered_recipients = []
    for r in recipients:
        ([r_public_key], voting_power) = r
        altered_recipients.append(([r_public_key], voting_power - 1))

    # Create a transaction which doesn't enfore the network power
    tx_election = ValidatorElection.generate([node_key.public_key], altered_recipients, new_validator, None).sign(
        [node_key.private_key]
    )

    with pytest.raises(UnequalValidatorSet):
        b_mock.validate_election(tx_election)


def test_get_status_ongoing(b, ongoing_validator_election, new_validator):
    status = ValidatorElection.ONGOING
    resp = b.get_election_status(ongoing_validator_election)
    assert resp == status


def test_get_status_concluded(b, concluded_election, new_validator):
    status = ValidatorElection.CONCLUDED
    resp = b.get_election_status(concluded_election)
    assert resp == status


def test_get_status_inconclusive(b, inconclusive_election, new_validator):
    def set_block_height_to_3():
        return {"height": 3}

    def custom_mock_get_validators(height):
        if height >= 3:
            return [
                {
                    "pub_key": {"data": "zL/DasvKulXZzhSNFwx4cLRXKkSM9GPK7Y0nZ4FEylM=", "type": "AC26791624DE60"},
                    "voting_power": 15,
                },
                {
                    "pub_key": {"data": "GIijU7GBcVyiVUcB0GwWZbxCxdk2xV6pxdvL24s/AqM=", "type": "AC26791624DE60"},
                    "voting_power": 7,
                },
                {
                    "pub_key": {"data": "JbfwrLvCVIwOPm8tj8936ki7IYbmGHjPiKb6nAZegRA=", "type": "AC26791624DE60"},
                    "voting_power": 10,
                },
                {
                    "pub_key": {"data": "PecJ58SaNRsWJZodDmqjpCWqG6btdwXFHLyE40RYlYM=", "type": "AC26791624DE60"},
                    "voting_power": 8,
                },
            ]
        else:
            return [
                {
                    "pub_key": {"data": "zL/DasvKulXZzhSNFwx4cLRXKkSM9GPK7Y0nZ4FEylM=", "type": "AC26791624DE60"},
                    "voting_power": 9,
                },
                {
                    "pub_key": {"data": "GIijU7GBcVyiVUcB0GwWZbxCxdk2xV6pxdvL24s/AqM=", "type": "AC26791624DE60"},
                    "voting_power": 7,
                },
                {
                    "pub_key": {"data": "JbfwrLvCVIwOPm8tj8936ki7IYbmGHjPiKb6nAZegRA=", "type": "AC26791624DE60"},
                    "voting_power": 10,
                },
                {
                    "pub_key": {"data": "PecJ58SaNRsWJZodDmqjpCWqG6btdwXFHLyE40RYlYM=", "type": "AC26791624DE60"},
                    "voting_power": 8,
                },
            ]

    b.get_validators = custom_mock_get_validators
    b.get_latest_block = set_block_height_to_3
    status = ValidatorElection.INCONCLUSIVE
    resp = b.get_election_status(inconclusive_election)
    assert resp == status


def test_upsert_validator_show(caplog, ongoing_validator_election, b):
    from planetmint.commands.planetmint import run_election_show

    election_id = ongoing_validator_election.id
    public_key = public_key_to_base64(ongoing_validator_election.assets[0]["data"]["public_key"]["value"])
    power = ongoing_validator_election.assets[0]["data"]["power"]
    node_id = ongoing_validator_election.assets[0]["data"]["node_id"]
    status = ValidatorElection.ONGOING

    show_args = Namespace(action="show", election_id=election_id)

    msg = run_election_show(show_args, b)

    assert msg == f"public_key={public_key}\npower={power}\nnode_id={node_id}\nstatus={status}"
