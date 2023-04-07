# Copyright © 2020 Interplanetary Database Association e.V.,
# Planetmint and IPDB software contributors.
# SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
# Code is Apache-2.0 and docs are CC-BY-4.0

import pytest

from transactions.common.transaction import TransactionLink
from transactions.types.assets.create import Create
from transactions.types.assets.transfer import Transfer

pytestmark = pytest.mark.bdb


@pytest.fixture
def txns(b, user_pk, user_sk, user2_pk, user2_sk, test_models):
    txs = [
        Create.generate([user_pk], [([user2_pk], 1)]).sign([user_sk]),
        Create.generate([user2_pk], [([user_pk], 1)]).sign([user2_sk]),
        Create.generate([user_pk], [([user_pk], 1), ([user2_pk], 1)]).sign([user_sk]),
    ]
    b.models.store_bulk_transactions(txs)
    return txs


def test_get_outputs_by_public_key(b, user_pk, user2_pk, txns, test_models):
    expected = [TransactionLink(txns[1].id, 0), TransactionLink(txns[2].id, 0)]
    actual = test_models.fastquery.get_outputs_by_public_key(user_pk)

    _all_txs = set([tx.txid for tx in expected + actual])
    assert len(_all_txs) == 2
    # assert b.models.fastquery.get_outputs_by_public_key(user_pk) == [ # OLD VERIFICATION
    #     TransactionLink(txns[1].id, 0),
    #     TransactionLink(txns[2].id, 0)
    # ]
    actual_1 = test_models.fastquery.get_outputs_by_public_key(user2_pk)
    expected_1 = [
        TransactionLink(txns[0].id, 0),
        TransactionLink(txns[2].id, 1),
    ]
    _all_tx_1 = set([tx.txid for tx in actual_1 + expected_1])
    assert len(_all_tx_1) == 2
    # assert b.models.fastquery.get_outputs_by_public_key(user2_pk) == [ # OLD VERIFICATION
    #     TransactionLink(txns[0].id, 0),
    #     TransactionLink(txns[2].id, 1),
    # ]


def test_filter_spent_outputs(b, user_pk, user_sk, test_models):
    out = [([user_pk], 1)]
    tx1 = Create.generate([user_pk], out * 2)
    tx1.sign([user_sk])

    inputs = tx1.to_inputs()

    tx2 = Transfer.generate([inputs[0]], out, [tx1.id])
    tx2.sign([user_sk])

    # tx2 produces a new unspent. inputs[1] remains unspent.
    b.models.store_bulk_transactions([tx1, tx2])

    outputs = test_models.fastquery.get_outputs_by_public_key(user_pk)
    unspents = test_models.fastquery.filter_spent_outputs(outputs)

    assert set(unsp for unsp in unspents) == {
        inputs[1].fulfills,
        tx2.to_inputs()[0].fulfills,
    }


def test_filter_unspent_outputs(b, user_pk, user_sk, test_models):
    out = [([user_pk], 1)]
    tx1 = Create.generate([user_pk], out * 2)
    tx1.sign([user_sk])

    inputs = tx1.to_inputs()

    tx2 = Transfer.generate([inputs[0]], out, [tx1.id])
    tx2.sign([user_sk])

    # tx2 produces a new unspent. input[1] remains unspent.
    b.models.store_bulk_transactions([tx1, tx2])

    outputs = test_models.fastquery.get_outputs_by_public_key(user_pk)
    spents = test_models.fastquery.filter_unspent_outputs(outputs)

    assert set(sp for sp in spents) == {
        inputs[0].fulfills,
    }


def test_outputs_query_key_order(b, user_pk, user_sk, user2_pk, test_validator):
    tx1 = Create.generate([user_pk], [([user_pk], 3), ([user_pk], 2), ([user_pk], 1)]).sign([user_sk])
    b.models.store_bulk_transactions([tx1])

    inputs = tx1.to_inputs()
    tx2 = Transfer.generate([inputs[1]], [([user2_pk], 2)], [tx1.id]).sign([user_sk])
    assert test_validator.validate_transaction(tx2)

    b.models.store_bulk_transactions([tx2])

    outputs = b.models.get_outputs_filtered(user_pk, spent=False)
    assert len(outputs) == 2

    outputs = b.models.get_outputs_filtered(user2_pk, spent=False)
    assert len(outputs) == 1

    # clean the transaction, metdata and asset collection
    b.models.delete_transactions([tx1.id, tx2.id])

    b.models.store_bulk_transactions([tx1, tx2])

    outputs = b.models.get_outputs_filtered(user_pk, spent=False)
    assert len(outputs) == 2

    outputs = b.models.get_outputs_filtered(user2_pk, spent=False)
    assert len(outputs) == 1
