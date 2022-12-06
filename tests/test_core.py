# Copyright � 2020 Interplanetary Database Association e.V.,
# Planetmint and IPDB software contributors.
# SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
# Code is Apache-2.0 and docs are CC-BY-4.0

import pytest

from planetmint.version import __tm_supported_versions__
from transactions.types.assets.create import Create
from transactions.types.assets.transfer import Transfer


@pytest.fixture
def config(request, monkeypatch):
    backend = request.config.getoption("--database-backend")
    if backend == "mongodb-ssl":
        backend = "mongodb"

    config = {
        "database": {
            "backend": backend,
            "host": "tarantool",
            "port": 3303,
            "name": "bigchain",
            "replicaset": "bigchain-rs",
            "connection_timeout": 5000,
            "max_tries": 3,
            "name": "bigchain",
        },
        "tendermint": {
            "host": "tendermint",
            "port": 26657,
        },
        "CONFIGURED": True,
    }

    monkeypatch.setattr("planetmint.config", config)
    return config


def test_bigchain_class_default_initialization(config):
    from planetmint import Planetmint
    from planetmint.validation import BaseValidationRules

    planet = Planetmint()
    assert planet.connection.host == config["database"]["host"]
    assert planet.connection.port == config["database"]["port"]
    assert planet.validation == BaseValidationRules


@pytest.mark.bdb
def test_get_spent_issue_1271(b, alice, bob, carol):
    tx_1 = Create.generate(
        [carol.public_key],
        [([carol.public_key], 8)],
    ).sign([carol.private_key])
    assert b.validate_transaction(tx_1)
    b.store_bulk_transactions([tx_1])

    tx_2 = Transfer.generate(
        tx_1.to_inputs(),
        [([bob.public_key], 2), ([alice.public_key], 2), ([carol.public_key], 4)],
        asset_ids=[tx_1.id],
    ).sign([carol.private_key])
    assert b.validate_transaction(tx_2)
    b.store_bulk_transactions([tx_2])

    tx_3 = Transfer.generate(
        tx_2.to_inputs()[2:3],
        [([alice.public_key], 1), ([carol.public_key], 3)],
        asset_ids=[tx_1.id],
    ).sign([carol.private_key])
    assert b.validate_transaction(tx_3)
    b.store_bulk_transactions([tx_3])

    tx_4 = Transfer.generate(
        tx_2.to_inputs()[1:2] + tx_3.to_inputs()[0:1],
        [([bob.public_key], 3)],
        asset_ids=[tx_1.id],
    ).sign([alice.private_key])
    assert b.validate_transaction(tx_4)
    b.store_bulk_transactions([tx_4])

    tx_5 = Transfer.generate(
        tx_2.to_inputs()[0:1],
        [([alice.public_key], 2)],
        asset_ids=[tx_1.id],
    ).sign([bob.private_key])
    assert b.validate_transaction(tx_5)

    b.store_bulk_transactions([tx_5])
    assert b.get_spent(tx_2.id, 0) == tx_5
    assert not b.get_spent(tx_5.id, 0)
    assert b.get_outputs_filtered(alice.public_key)
    assert b.get_outputs_filtered(alice.public_key, spent=False)
