# Copyright © 2020 Interplanetary Database Association e.V.,
# Planetmint and IPDB software contributors.
# SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
# Code is Apache-2.0 and docs are CC-BY-4.0

from copy import deepcopy

import pytest
import json
from transactions.common.transaction import Transaction
from transactions.types.assets.create import Create
from transactions.types.assets.transfer import Transfer
from planetmint.backend.interfaces import Asset, MetaData
from planetmint.backend.models import DbTransaction

pytestmark = pytest.mark.bdb


def test_get_txids_filtered(signed_create_tx, signed_transfer_tx, db_conn):
    from planetmint.backend.tarantool import query

    # create and insert two blocks, one for the create and one for the
    # transfer transaction
    create_tx_dict = signed_create_tx.to_dict()
    transfer_tx_dict = signed_transfer_tx.to_dict()

    query.store_transactions(signed_transactions=[create_tx_dict], connection=db_conn)
    query.store_transactions(signed_transactions=[transfer_tx_dict], connection=db_conn)

    asset_id = Transaction.get_asset_id([signed_create_tx, signed_transfer_tx])

    # Test get by just asset id
    txids = set(query.get_txids_filtered(connection=db_conn, asset_ids=[asset_id]))
    assert txids == {signed_create_tx.id, signed_transfer_tx.id}

    # Test get by asset and CREATE
    txids = set(query.get_txids_filtered(connection=db_conn, asset_ids=[asset_id], operation=Transaction.CREATE))
    assert txids == {signed_create_tx.id}

    # Test get by asset and TRANSFER
    txids = set(query.get_txids_filtered(connection=db_conn, asset_ids=[asset_id], operation=Transaction.TRANSFER))
    assert txids == {signed_transfer_tx.id}


def test_get_owned_ids(signed_create_tx, user_pk, db_conn):
    from planetmint.backend.tarantool import query

    # insert a transaction
    query.store_transactions(connection=db_conn, signed_transactions=[signed_create_tx.to_dict()])

    txns = query.get_owned_ids(connection=db_conn, owner=user_pk)
    tx_dict = signed_create_tx.to_dict()
    owned_tx = DbTransaction.remove_generated_fields(txns[0].to_dict())
    assert owned_tx == tx_dict


def test_store_block(db_conn):
    from planetmint.lib import Block
    from planetmint.backend.tarantool import query

    block = Block(app_hash="random_utxo", height=3, transactions=[])
    query.store_block(connection=db_conn, block=block._asdict())
    # block = query.get_block(connection=db_conn)
    blocks = db_conn.run(db_conn.space("blocks").select([]))
    assert len(blocks) == 1


def test_get_block(db_conn):
    from planetmint.lib import Block
    from planetmint.backend.tarantool import query

    block = Block(app_hash="random_utxo", height=3, transactions=[])

    query.store_block(connection=db_conn, block=block._asdict())

    block = dict(query.get_block(connection=db_conn, block_id=3))
    assert block["height"] == 3


def test_store_pre_commit_state(db_conn):
    from planetmint.backend.tarantool import query

    state = dict(height=3, transactions=[])

    query.store_pre_commit_state(connection=db_conn, state=state)
    commit = query.get_pre_commit_state(connection=db_conn)
    assert len([commit]) == 1

    # cursor = db_context.conn.db.pre_commit.find({'commit_id': 'test'},
    # projection={'_id': False})


def test_get_pre_commit_state(db_conn):
    from planetmint.backend.tarantool import query

    all_pre = db_conn.run(db_conn.space("pre_commits").select([]))
    for pre in all_pre:
        db_conn.run(db_conn.space("pre_commits").delete(pre[0]), only_data=False)
    #  TODO First IN, First OUT
    state = dict(height=3, transactions=[])
    # db_context.conn.db.pre_commit.insert_one
    query.store_pre_commit_state(state=state, connection=db_conn)
    resp = query.get_pre_commit_state(connection=db_conn)
    assert resp == state


def test_validator_update(db_conn):
    from planetmint.backend.tarantool import query

    def gen_validator_update(height):
        return {"validators": [], "height": height, "election_id": f"election_id_at_height_{height}"}
        # return {'data': 'somedata', 'height': height, 'election_id': f'election_id_at_height_{height}'}

    for i in range(1, 100, 10):
        value = gen_validator_update(i)
        query.store_validator_set(conn=db_conn, validators_update=value)

    v1 = query.get_validator_set(connection=db_conn, height=8)
    assert v1["height"] == 1

    v41 = query.get_validator_set(connection=db_conn, height=50)
    assert v41["height"] == 41

    v91 = query.get_validator_set(connection=db_conn)
    assert v91["height"] == 91


@pytest.mark.parametrize(
    "description,stores,expected",
    [
        (
            "Query empty database.",
            [],
            None,
        ),
        (
            "Store one chain with the default value for `is_synced`.",
            [
                {"height": 0, "chain_id": "some-id"},
            ],
            {"height": 0, "chain_id": "some-id", "is_synced": True},
        ),
        (
            "Store one chain with a custom value for `is_synced`.",
            [
                {"height": 0, "chain_id": "some-id", "is_synced": False},
            ],
            {"height": 0, "chain_id": "some-id", "is_synced": False},
        ),
        (
            "Store one chain, then update it.",
            [
                {"height": 0, "chain_id": "some-id", "is_synced": True},
                {"height": 0, "chain_id": "new-id", "is_synced": False},
            ],
            {"height": 0, "chain_id": "new-id", "is_synced": False},
        ),
        (
            "Store a chain, update it, store another chain.",
            [
                {"height": 0, "chain_id": "some-id", "is_synced": True},
                {"height": 0, "chain_id": "some-id", "is_synced": False},
                {"height": 10, "chain_id": "another-id", "is_synced": True},
            ],
            {"height": 10, "chain_id": "another-id", "is_synced": True},
        ),
    ],
)
def test_store_abci_chain(description, stores, expected, db_conn):
    from planetmint.backend.tarantool import query

    for store in stores:
        query.store_abci_chain(db_conn, **store)

    actual = query.get_latest_abci_chain(db_conn)
    assert expected == actual, description
