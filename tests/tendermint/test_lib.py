# Copyright © 2020 Interplanetary Database Association e.V.,
# Planetmint and IPDB software contributors.
# SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
# Code is Apache-2.0 and docs are CC-BY-4.0


import os
import pytest

from unittest.mock import patch
from transactions.types.assets.create import Create
from transactions.types.assets.transfer import Transfer
from hashlib import sha3_256
from planetmint import backend
from transactions.common.transaction_mode_types import (
    BROADCAST_TX_COMMIT,
    BROADCAST_TX_ASYNC,
    BROADCAST_TX_SYNC,
)
from planetmint.abci.block import Block
from ipld import marshal, multihash
from uuid import uuid4

from planetmint.abci.rpc import MODE_COMMIT, MODE_LIST
from tests.utils import delete_unspent_outputs, get_utxoset_merkle_root, store_unspent_outputs, update_utxoset


@pytest.mark.bdb
def test_asset_is_separated_from_transaciton(b):
    import copy
    from transactions.common.crypto import generate_key_pair
    from planetmint.backend.tarantool.connection import TarantoolDBConnection

    if isinstance(b.models.connection, TarantoolDBConnection):
        pytest.skip("This specific function is skipped because, assets are stored differently if using Tarantool")

    alice = generate_key_pair()
    bob = generate_key_pair()

    assets = [
        {
            "data": multihash(
                marshal(
                    {
                        "Never gonna": [
                            "give you up",
                            "let you down",
                            "run around" "desert you",
                            "make you cry",
                            "say goodbye",
                            "tell a lie",
                            "hurt you",
                        ]
                    }
                )
            )
        }
    ]

    tx = Create.generate([alice.public_key], [([bob.public_key], 1)], metadata=None, assets=assets).sign(
        [alice.private_key]
    )

    # with b.models.store_bulk_transactions we use `insert_many` where PyMongo
    # automatically adds an `_id` field to the tx, therefore we need the
    # deepcopy, for more info see:
    # https://api.mongodb.com/python/current/faq.html#writes-and-ids
    tx_dict = copy.deepcopy(tx.to_dict())

    b.models.store_bulk_transactions([tx])
    assert "asset" not in backend.query.get_transaction_single(b.models.connection, tx.id)
    assert backend.query.get_asset(b.models.connection, tx.id).data == assets[0]
    assert b.models.get_transaction(tx.id).to_dict() == tx_dict


@pytest.mark.bdb
def test_get_latest_block(b):
    from planetmint.abci.block import Block

    for i in range(10):
        app_hash = os.urandom(16).hex()
        txn_id = os.urandom(16).hex()
        block = Block(app_hash=app_hash, height=i, transactions=[txn_id])._asdict()
        b.models.store_block(block)

    block = b.models.get_latest_block()
    assert block["height"] == 9


def test_validation_error(b):
    from transactions.common.crypto import generate_key_pair

    alice = generate_key_pair()
    tx = (
        Create.generate([alice.public_key], [([alice.public_key], 1)], assets=None).sign([alice.private_key]).to_dict()
    )

    tx["metadata"] = ""
    assert not b.validate_transaction(tx)


@patch("requests.post")
def test_write_and_post_transaction(mock_post, b, test_abci_rpc):
    from transactions.common.crypto import generate_key_pair
    from planetmint.abci.utils import encode_transaction

    alice = generate_key_pair()
    tx = (
        Create.generate([alice.public_key], [([alice.public_key], 1)], assets=None).sign([alice.private_key]).to_dict()
    )

    tx = b.validate_transaction(tx)
    test_abci_rpc.write_transaction(
        MODE_LIST, test_abci_rpc.tendermint_rpc_endpoint, MODE_COMMIT, tx, BROADCAST_TX_ASYNC
    )

    assert mock_post.called
    args, kwargs = mock_post.call_args
    assert BROADCAST_TX_ASYNC == kwargs["json"]["method"]
    encoded_tx = [encode_transaction(tx.to_dict())]
    assert encoded_tx == kwargs["json"]["params"]


@patch("requests.post")
@pytest.mark.parametrize("mode", [BROADCAST_TX_SYNC, BROADCAST_TX_ASYNC, BROADCAST_TX_COMMIT])
def test_post_transaction_valid_modes(mock_post, b, mode, test_abci_rpc):
    from transactions.common.crypto import generate_key_pair

    alice = generate_key_pair()
    tx = (
        Create.generate([alice.public_key], [([alice.public_key], 1)], assets=None).sign([alice.private_key]).to_dict()
    )
    tx = b.validate_transaction(tx)
    test_abci_rpc.write_transaction(MODE_LIST, test_abci_rpc.tendermint_rpc_endpoint, MODE_COMMIT, tx, mode)

    args, kwargs = mock_post.call_args
    assert mode == kwargs["json"]["method"]


def test_post_transaction_invalid_mode(b, test_abci_rpc):
    from transactions.common.crypto import generate_key_pair
    from transactions.common.exceptions import ValidationError

    alice = generate_key_pair()
    tx = (
        Create.generate([alice.public_key], [([alice.public_key], 1)], assets=None).sign([alice.private_key]).to_dict()
    )
    tx = b.validate_transaction(tx)
    with pytest.raises(ValidationError):
        test_abci_rpc.write_transaction(MODE_LIST, test_abci_rpc.tendermint_rpc_endpoint, MODE_COMMIT, tx, "nope")


@pytest.mark.bdb
def test_update_utxoset(b, signed_create_tx, signed_transfer_tx, db_conn):
    update_utxoset(b.models.connection, signed_create_tx)
    utxoset = db_conn.get_space("utxos")
    assert utxoset.select().rowcount == 1
    utxo = utxoset.select().data
    assert utxo[0][1] == signed_create_tx.id
    assert utxo[0][2] == 0
    update_utxoset(b.models.connection, signed_transfer_tx)
    assert utxoset.select().rowcount == 1
    utxo = utxoset.select().data
    assert utxo[0][1] == signed_transfer_tx.id
    assert utxo[0][2] == 0


@pytest.mark.bdb
def test_store_transaction(mocker, b, signed_create_tx, signed_transfer_tx):
    mocked_store_transaction = mocker.patch("planetmint.backend.query.store_transactions")
    b.models.store_bulk_transactions([signed_create_tx])
    mocked_store_transaction.assert_any_call(b.models.connection, [signed_create_tx.to_dict()], "transactions")
    mocked_store_transaction.reset_mock()
    b.models.store_bulk_transactions([signed_transfer_tx])


@pytest.mark.bdb
def test_store_bulk_transaction(mocker, b, signed_create_tx, signed_transfer_tx):
    mocked_store_transactions = mocker.patch("planetmint.backend.query.store_transactions")
    b.models.store_bulk_transactions((signed_create_tx,))
    mocked_store_transactions.assert_any_call(b.models.connection, [signed_create_tx.to_dict()], "transactions")
    mocked_store_transactions.reset_mock()
    b.models.store_bulk_transactions((signed_transfer_tx,))


@pytest.mark.bdb
def test_delete_zero_unspent_outputs(b, utxoset):
    unspent_outputs, utxo_collection = utxoset
    num_rows_before_operation = utxo_collection.select().rowcount
    delete_res = delete_unspent_outputs(b.models.connection)  # noqa: F841
    num_rows_after_operation = utxo_collection.select().rowcount
    # assert delete_res is None
    assert num_rows_before_operation == num_rows_after_operation


@pytest.mark.bdb
def test_delete_one_unspent_outputs(b, dummy_unspent_outputs):
    utxo_space = b.models.connection.get_space("utxos")
    for utxo in dummy_unspent_outputs:
        res = utxo_space.insert((uuid4().hex, utxo["transaction_id"], utxo["output_index"], utxo))
        assert res

    delete_unspent_outputs(b.models.connection, dummy_unspent_outputs[0])
    res1 = utxo_space.select(["a", 1], index="utxo_by_transaction_id_and_output_index").data
    res2 = utxo_space.select(["b", 0], index="utxo_by_transaction_id_and_output_index").data
    assert len(res1) + len(res2) == 2
    res3 = utxo_space.select(["a", 0], index="utxo_by_transaction_id_and_output_index").data
    assert len(res3) == 0


@pytest.mark.bdb
def test_delete_many_unspent_outputs(b, dummy_unspent_outputs):
    utxo_space = b.models.connection.get_space("utxos")
    for utxo in dummy_unspent_outputs:
        res = utxo_space.insert((uuid4().hex, utxo["transaction_id"], utxo["output_index"], utxo))
        assert res

    delete_unspent_outputs(b.models.connection, *dummy_unspent_outputs[::2])
    res1 = utxo_space.select(["a", 0], index="utxo_by_transaction_id_and_output_index").data
    res2 = utxo_space.select(["b", 0], index="utxo_by_transaction_id_and_output_index").data
    assert len(res1) + len(res2) == 0
    res3 = utxo_space.select([], index="utxo_by_transaction_id_and_output_index").data
    assert len(res3) == 1


@pytest.mark.bdb
def test_store_zero_unspent_output(b):
    utxos = b.models.connection.get_space("utxos")
    num_rows_before_operation = utxos.select().rowcount
    res = store_unspent_outputs(b.models.connection)
    num_rows_after_operation = utxos.select().rowcount
    assert res is None
    assert num_rows_before_operation == num_rows_after_operation


@pytest.mark.bdb
def test_store_one_unspent_output(b, unspent_output_1, utxo_collection):
    from planetmint.backend.tarantool.connection import TarantoolDBConnection

    res = store_unspent_outputs(b.models.connection, unspent_output_1)
    if not isinstance(b.models.connection, TarantoolDBConnection):
        assert res.acknowledged
        assert len(list(res)) == 1
        assert (
            utxo_collection.count_documents(
                {
                    "transaction_id": unspent_output_1["transaction_id"],
                    "output_index": unspent_output_1["output_index"],
                }
            )
            == 1
        )
    else:
        utx_space = b.models.connection.get_space("utxos")
        res = utx_space.select(
            [unspent_output_1["transaction_id"], unspent_output_1["output_index"]],
            index="utxo_by_transaction_id_and_output_index",
        )
        assert len(res.data) == 1


@pytest.mark.bdb
def test_store_many_unspent_outputs(b, unspent_outputs):
    store_unspent_outputs(b.models.connection, *unspent_outputs)
    utxo_space = b.models.connection.get_space("utxos")
    res = utxo_space.select([unspent_outputs[0]["transaction_id"]], index="utxos_by_transaction_id")
    assert len(res.data) == 3


def test_get_utxoset_merkle_root_when_no_utxo(b):
    assert get_utxoset_merkle_root(b.models.connection) == sha3_256(b"").hexdigest()


@pytest.mark.bdb
def test_get_utxoset_merkle_root(b, dummy_unspent_outputs):
    utxo_space = b.models.connection.get_space("utxos")
    for utxo in dummy_unspent_outputs:
        res = utxo_space.insert((uuid4().hex, utxo["transaction_id"], utxo["output_index"], utxo))
        assert res

    expected_merkle_root = "86d311c03115bf4d287f8449ca5828505432d69b82762d47077b1c00fe426eac"
    merkle_root = get_utxoset_merkle_root(b.models.connection)
    assert merkle_root == expected_merkle_root


@pytest.mark.bdb
def test_get_spent_transaction_double_spend(b, alice, bob, carol):
    from transactions.common.exceptions import DoubleSpend

    assets = [{"data": multihash(marshal({"test": "asset"}))}]

    tx = Create.generate([alice.public_key], [([alice.public_key], 1)], assets=assets).sign([alice.private_key])

    tx_transfer = Transfer.generate(tx.to_inputs(), [([bob.public_key], 1)], asset_ids=[tx.id]).sign(
        [alice.private_key]
    )

    double_spend = Transfer.generate(tx.to_inputs(), [([carol.public_key], 1)], asset_ids=[tx.id]).sign(
        [alice.private_key]
    )

    same_input_double_spend = Transfer.generate(
        tx.to_inputs() + tx.to_inputs(), [([bob.public_key], 1)], asset_ids=[tx.id]
    ).sign([alice.private_key])

    b.models.store_bulk_transactions([tx])

    with pytest.raises(DoubleSpend):
        b.validate_transaction(same_input_double_spend)

    assert b.models.get_spent(tx.id, tx_transfer.inputs[0].fulfills.output, [tx_transfer])

    with pytest.raises(DoubleSpend):
        b.models.get_spent(tx.id, tx_transfer.inputs[0].fulfills.output, [tx_transfer, double_spend])

    b.models.store_bulk_transactions([tx_transfer])

    with pytest.raises(DoubleSpend):
        b.models.get_spent(tx.id, tx_transfer.inputs[0].fulfills.output, [double_spend])


def test_validation_with_transaction_buffer(b):
    from transactions.common.crypto import generate_key_pair

    priv_key, pub_key = generate_key_pair()

    create_tx = Create.generate([pub_key], [([pub_key], 10)]).sign([priv_key])
    transfer_tx = Transfer.generate(create_tx.to_inputs(), [([pub_key], 10)], asset_ids=[create_tx.id]).sign(
        [priv_key]
    )
    double_spend = Transfer.generate(create_tx.to_inputs(), [([pub_key], 10)], asset_ids=[create_tx.id]).sign(
        [priv_key]
    )

    assert b.is_valid_transaction(create_tx)
    assert b.is_valid_transaction(transfer_tx, [create_tx])

    assert not b.is_valid_transaction(create_tx, [create_tx])
    assert not b.is_valid_transaction(transfer_tx, [create_tx, transfer_tx])
    assert not b.is_valid_transaction(double_spend, [create_tx, transfer_tx])


@pytest.mark.bdb
def test_migrate_abci_chain_yields_on_genesis(b):
    b.migrate_abci_chain()
    latest_chain = b.models.get_latest_abci_chain()
    assert latest_chain is None


@pytest.mark.bdb
@pytest.mark.parametrize(
    "chain,block_height,expected",
    [
        (
            (1, "chain-XYZ", True),
            4,
            {"height": 5, "chain_id": "chain-XYZ-migrated-at-height-4", "is_synced": False},
        ),
        (
            (5, "chain-XYZ-migrated-at-height-4", True),
            13,
            {"height": 14, "chain_id": "chain-XYZ-migrated-at-height-13", "is_synced": False},
        ),
    ],
)
def test_migrate_abci_chain_generates_new_chains(b, chain, block_height, expected):
    b.models.store_abci_chain(*chain)
    b.models.store_block(Block(app_hash="", height=block_height, transactions=[])._asdict())
    b.migrate_abci_chain()
    latest_chain = b.models.get_latest_abci_chain()
    assert latest_chain == expected


@pytest.mark.bdb
def test_get_spent_key_order(b, user_pk, user_sk, user2_pk, user2_sk):
    from transactions.common.crypto import generate_key_pair
    from transactions.common.exceptions import DoubleSpend

    alice = generate_key_pair()
    bob = generate_key_pair()

    tx1 = Create.generate([user_pk], [([alice.public_key], 3), ([user_pk], 2)]).sign([user_sk])
    b.models.store_bulk_transactions([tx1])

    inputs = tx1.to_inputs()
    tx2 = Transfer.generate([inputs[1]], [([user2_pk], 2)], [tx1.id]).sign([user_sk])
    assert b.validate_transaction(tx2)

    b.models.store_bulk_transactions([tx2])

    tx3 = Transfer.generate([inputs[1]], [([bob.public_key], 2)], [tx1.id]).sign([user_sk])

    with pytest.raises(DoubleSpend):
        b.validate_transaction(tx3)
