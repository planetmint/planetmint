# Copyright © 2020 Interplanetary Database Association e.V.,
# Planetmint and IPDB software contributors.
# SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
# Code is Apache-2.0 and docs are CC-BY-4.0

import pytest

from argparse import Namespace
from unittest.mock import patch
from planetmint.abci.utils import public_key_to_base64
from transactions.types.elections.validator_election import ValidatorElection
from transactions.common.exceptions import (
    DuplicateTransaction,
    UnequalValidatorSet,
    InvalidProposer,
    MultipleInputsError,
    InvalidPowerChange,
)


pytestmark = pytest.mark.bdb


def test_upsert_validator_valid_election(monkeypatch, b, network_validators, new_validator, node_key):
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
        election = ValidatorElection.generate([node_key.public_key], voters, new_validator, None).sign(
            [node_key.private_key]
        )
        assert b.validate_election(election)
        m.undo()


def test_upsert_validator_invalid_election_public_key(monkeypatch, b, network_validators, new_validator, node_key):
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
        from transactions.common.exceptions import InvalidPublicKey

        for iv in ["ed25519-base32", "ed25519-base64"]:
            new_validator[0]["data"]["public_key"]["type"] = iv
            voters = b.get_recipients_list()

            with pytest.raises(InvalidPublicKey):
                ValidatorElection.generate([node_key.public_key], voters, new_validator, None).sign(
                    [node_key.private_key]
                )
        m.undo()


def test_upsert_validator_invalid_power_election(monkeypatch, b, network_validators, new_validator, node_key):
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
        new_validator[0]["data"]["power"] = 30

        election = ValidatorElection.generate([node_key.public_key], voters, new_validator, None).sign(
            [node_key.private_key]
        )
        with pytest.raises(InvalidPowerChange):
            b.validate_election(election)
        m.undo()


def test_upsert_validator_invalid_proposed_election(monkeypatch, b, network_validators, new_validator, node_key):
    from transactions.common.crypto import generate_key_pair

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

        alice = generate_key_pair()
        voters = b.get_recipients_list()
        election = ValidatorElection.generate([alice.public_key], voters, new_validator, None).sign(
            [alice.private_key]
        )
        with pytest.raises(InvalidProposer):
            b.validate_election(election)


def test_upsert_validator_invalid_inputs_election(monkeypatch, b, network_validators, new_validator, node_key):
    from transactions.common.crypto import generate_key_pair

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
        alice = generate_key_pair()
        voters = b.get_recipients_list()
        election = ValidatorElection.generate(
            [node_key.public_key, alice.public_key], voters, new_validator, None
        ).sign([node_key.private_key, alice.private_key])
        with pytest.raises(MultipleInputsError):
            b.validate_election(election)
        m.undo()


@patch("transactions.types.elections.election.uuid4", lambda: "mock_uuid4")
def test_upsert_validator_invalid_election(monkeypatch, b, network_validators, new_validator, node_key):
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
        duplicate_election = ValidatorElection.generate([node_key.public_key], voters, new_validator, None).sign(
            [node_key.private_key]
        )
        voters = b.get_recipients_list()
        fixed_seed_election = ValidatorElection.generate([node_key.public_key], voters, new_validator, None).sign(
            [node_key.private_key]
        )

        with pytest.raises(DuplicateTransaction):
            b.validate_election(fixed_seed_election, [duplicate_election])

        b.models.store_bulk_transactions([fixed_seed_election])

        with pytest.raises(DuplicateTransaction):
            b.validate_election(duplicate_election)

        # Try creating an election with incomplete voter set
        invalid_election = ValidatorElection.generate([node_key.public_key], voters[1:], new_validator, None).sign(
            [node_key.private_key]
        )

        with pytest.raises(UnequalValidatorSet):
            b.validate_election(invalid_election)

        recipients = b.get_recipients_list()
        altered_recipients = []
        for r in recipients:
            ([r_public_key], voting_power) = r
            altered_recipients.append(([r_public_key], voting_power - 1))

        # Create a transaction which doesn't enfore the network power
        tx_election = ValidatorElection.generate([node_key.public_key], altered_recipients, new_validator, None).sign(
            [node_key.private_key]
        )

        with pytest.raises(UnequalValidatorSet):
            b.validate_election(tx_election)
        m.undo()


def test_get_status_ongoing(monkeypatch, b, network_validators, node_key, new_validator, ed25519_node_keys):
    def mock_get_validators(self, height):
        _validators = []
        for public_key, power in network_validators.items():
            _validators.append(
                {
                    "public_key": {"type": "ed25519-base64", "value": public_key},
                    "voting_power": power,
                }
            )
        return _validators

    with monkeypatch.context() as m:
        from planetmint.model.dataaccessor import DataAccessor
        from planetmint.backend import schema, query
        from planetmint.abci.block import Block

        m.setattr(DataAccessor, "get_validators", mock_get_validators)

        voters = b.get_recipients_list()
        valid_upsert_validator_election = ValidatorElection.generate(
            [node_key.public_key], voters, new_validator, None
        ).sign([node_key.private_key])

        validators = b.models.get_validators(height=1)
        genesis_validators = {"validators": validators, "height": 0}
        query.store_validator_set(b.models.connection, genesis_validators)
        b.models.store_bulk_transactions([valid_upsert_validator_election])
        query.store_election(b.models.connection, valid_upsert_validator_election.id, 1, is_concluded=False)
        block_1 = Block(app_hash="hash_1", height=1, transactions=[valid_upsert_validator_election.id])
        b.models.store_block(block_1._asdict())

        status = ValidatorElection.ONGOING
        resp = b.get_election_status(valid_upsert_validator_election)
        assert resp == status
        m.undo()


def test_get_status_concluded(monkeypatch, b, network_validators, node_key, new_validator, ed25519_node_keys):
    def mock_get_validators(self, height):
        _validators = []
        for public_key, power in network_validators.items():
            _validators.append(
                {
                    "public_key": {"type": "ed25519-base64", "value": public_key},
                    "voting_power": power,
                }
            )
        return _validators

    with monkeypatch.context() as m:
        from planetmint.model.dataaccessor import DataAccessor
        from planetmint.backend import schema, query
        from planetmint.abci.block import Block

        m.setattr(DataAccessor, "get_validators", mock_get_validators)

        voters = b.get_recipients_list()
        valid_upsert_validator_election = ValidatorElection.generate(
            [node_key.public_key], voters, new_validator, None
        ).sign([node_key.private_key])

        validators = b.models.get_validators(height=1)
        genesis_validators = {"validators": validators, "height": 0}
        query.store_validator_set(b.models.connection, genesis_validators)
        b.models.store_bulk_transactions([valid_upsert_validator_election])
        query.store_election(b.models.connection, valid_upsert_validator_election.id, 1, is_concluded=False)
        block_1 = Block(app_hash="hash_1", height=1, transactions=[valid_upsert_validator_election.id])
        b.models.store_block(block_1._asdict())
        query.store_election(b.models.connection, valid_upsert_validator_election.id, 2, is_concluded=True)

        status = ValidatorElection.CONCLUDED
        resp = b.get_election_status(valid_upsert_validator_election)
        assert resp == status
        m.undo()


def test_get_status_inconclusive(monkeypatch, b, network_validators, node_key, new_validator):
    def set_block_height_to_3(self):
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

    def mock_get_validators(self, height):
        _validators = []
        for public_key, power in network_validators.items():
            _validators.append(
                {
                    "public_key": {"type": "ed25519-base64", "value": public_key},
                    "voting_power": power,
                }
            )
        return _validators

    with monkeypatch.context() as m:
        from planetmint.model.dataaccessor import DataAccessor
        from planetmint.backend import schema, query
        from planetmint.abci.block import Block

        m.setattr(DataAccessor, "get_validators", mock_get_validators)

        voters = b.get_recipients_list()
        valid_upsert_validator_election = ValidatorElection.generate(
            [node_key.public_key], voters, new_validator, None
        ).sign([node_key.private_key])

        validators = b.models.get_validators(height=1)
        genesis_validators = {"validators": validators, "height": 0}
        query.store_validator_set(b.models.connection, genesis_validators)
        b.models.store_bulk_transactions([valid_upsert_validator_election])
        query.store_election(b.models.connection, valid_upsert_validator_election.id, 1, is_concluded=False)
        block_1 = Block(app_hash="hash_1", height=1, transactions=[valid_upsert_validator_election.id])
        b.models.store_block(block_1._asdict())

        validators = b.models.get_validators(height=1)
        validators[0]["voting_power"] = 15
        validator_update = {"validators": validators, "height": 2, "election_id": "some_other_election"}

        query.store_validator_set(b.models.connection, validator_update)
        m.undo()
    with monkeypatch.context() as m2:
        m2.setattr(DataAccessor, "get_validators", custom_mock_get_validators)
        m2.setattr(DataAccessor, "get_latest_block", set_block_height_to_3)
        status = ValidatorElection.INCONCLUSIVE
        resp = b.get_election_status(valid_upsert_validator_election)
        assert resp == status
        m2.undo()


def test_upsert_validator_show(monkeypatch, caplog, b, node_key, new_validator, network_validators):
    from planetmint.commands.planetmint import run_election_show

    def mock_get_validators(self, height):
        _validators = []
        for public_key, power in network_validators.items():
            _validators.append(
                {
                    "public_key": {"type": "ed25519-base64", "value": public_key},
                    "voting_power": power,
                }
            )
        return _validators

    with monkeypatch.context() as m:
        from planetmint.model.dataaccessor import DataAccessor
        from planetmint.backend import schema, query
        from planetmint.abci.block import Block

        m.setattr(DataAccessor, "get_validators", mock_get_validators)

        voters = b.get_recipients_list()
        valid_upsert_validator_election = ValidatorElection.generate(
            [node_key.public_key], voters, new_validator, None
        ).sign([node_key.private_key])

        validators = b.models.get_validators(height=1)
        genesis_validators = {"validators": validators, "height": 0}
        query.store_validator_set(b.models.connection, genesis_validators)
        b.models.store_bulk_transactions([valid_upsert_validator_election])
        query.store_election(b.models.connection, valid_upsert_validator_election.id, 1, is_concluded=False)
        block_1 = Block(app_hash="hash_1", height=1, transactions=[valid_upsert_validator_election.id])
        b.models.store_block(block_1._asdict())
        election_id = valid_upsert_validator_election.id
        public_key = public_key_to_base64(valid_upsert_validator_election.assets[0]["data"]["public_key"]["value"])
        power = valid_upsert_validator_election.assets[0]["data"]["power"]
        node_id = valid_upsert_validator_election.assets[0]["data"]["node_id"]
        status = ValidatorElection.ONGOING

        show_args = Namespace(action="show", election_id=election_id)

        msg = run_election_show(show_args, b)

        assert msg == f"public_key={public_key}\npower={power}\nnode_id={node_id}\nstatus={status}"
        m.undo()
