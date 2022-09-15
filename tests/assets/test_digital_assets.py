# Copyright © 2020 Interplanetary Database Association e.V.,
# Planetmint and IPDB software contributors.
# SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
# Code is Apache-2.0 and docs are CC-BY-4.0

import pytest
import random
from planetmint.transactions.types.assets.create import Create
from planetmint.transactions.types.assets.transfer import Transfer


def test_asset_transfer(b, signed_create_tx, user_pk, user_sk):
    tx_transfer = Transfer.generate(signed_create_tx.to_inputs(), [([user_pk], 1)], signed_create_tx.id)
    tx_transfer_signed = tx_transfer.sign([user_sk])

    b.store_bulk_transactions([signed_create_tx])

    assert tx_transfer_signed.validate(b) == tx_transfer_signed
    assert tx_transfer_signed.asset["id"] == signed_create_tx.id


def test_validate_transfer_asset_id_mismatch(b, signed_create_tx, user_pk, user_sk):
    from planetmint.transactions.common.exceptions import AssetIdMismatch

    tx_transfer = Transfer.generate(signed_create_tx.to_inputs(), [([user_pk], 1)], signed_create_tx.id)
    tx_transfer.asset["id"] = "a" * 64
    tx_transfer_signed = tx_transfer.sign([user_sk])

    b.store_bulk_transactions([signed_create_tx])

    with pytest.raises(AssetIdMismatch):
        tx_transfer_signed.validate(b)


def test_get_asset_id_create_transaction(alice, user_pk):
    from planetmint.transactions.common.transaction import Transaction

    tx_create = Create.generate([alice.public_key], [([user_pk], 1)])
    assert Transaction.get_asset_id(tx_create) == tx_create.id


def test_get_asset_id_transfer_transaction(b, signed_create_tx, user_pk):
    from planetmint.transactions.common.transaction import Transaction

    tx_transfer = Transfer.generate(signed_create_tx.to_inputs(), [([user_pk], 1)], signed_create_tx.id)
    asset_id = Transaction.get_asset_id(tx_transfer)
    assert asset_id == tx_transfer.asset["id"]


def test_asset_id_mismatch(alice, user_pk):
    from planetmint.transactions.common.transaction import Transaction
    from planetmint.transactions.common.exceptions import AssetIdMismatch

    tx1 = Create.generate(
        [alice.public_key], [([user_pk], 1)], metadata="QmaozNR7DZHQK1ZcU9p7QdrshMvXqWK6gpu5rmrkPdT3L4"
    )
    tx1.sign([alice.private_key])
    tx2 = Create.generate(
        [alice.public_key], [([user_pk], 1)], metadata="zb2rhe5P4gXftAwvA4eXQ5HJwsER2owDyS9sKaQRRVQPn93bA"
    )
    tx2.sign([alice.private_key])

    with pytest.raises(AssetIdMismatch):
        Transaction.get_asset_id([tx1, tx2])


def test_create_valid_divisible_asset(b, user_pk, user_sk):

    tx = Create.generate([user_pk], [([user_pk], 2)])
    tx_signed = tx.sign([user_sk])
    assert tx_signed.validate(b) == tx_signed
