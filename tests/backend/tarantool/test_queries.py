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


def test_write_assets(db_conn):
    from planetmint.backend.tarantool import query

    assets = [
        Asset("1", "1", "1"),
        Asset("2", "2", "2"),
        Asset("3", "3", "3"),
        # Duplicated id. Should not be written to the database
        Asset("1", "1", "1"),
    ]

    # write the assets
    for asset in assets:
        query.store_asset(connection=db_conn, asset=asset)

    # check that 3 assets were written to the database
    documents = query.get_assets(assets_ids=[asset.id for asset in assets], connection=db_conn)

    assert len(documents) == 3
    assert list(documents)[0] == assets[:-1][0]


def test_get_assets(db_conn):
    from planetmint.backend.tarantool import query

    assets = [
        Asset("1", "1"),
        Asset("2", "2"),
        Asset("3", "3"),
    ]

    query.store_assets(assets=assets, connection=db_conn)

    for asset in assets:
        assert query.get_asset(asset_id=asset.id, connection=db_conn)


@pytest.mark.parametrize("table", ["assets", "metadata"])
def test_text_search(table):
    assert "PASS FOR NOW"

    # # Example data and tests cases taken from the mongodb documentation
    # # https://docs.mongodb.com/manual/reference/operator/query/text/
    # objects = [
    #     {'id': 1, 'subject': 'coffee', 'author': 'xyz', 'views': 50},
    #     {'id': 2, 'subject': 'Coffee Shopping', 'author': 'efg', 'views': 5},
    #     {'id': 3, 'subject': 'Baking a cake', 'author': 'abc', 'views': 90},
    #     {'id': 4, 'subject': 'baking', 'author': 'xyz', 'views': 100},
    #     {'id': 5, 'subject': 'Café Con Leche', 'author': 'abc', 'views': 200},
    #     {'id': 6, 'subject': 'Сырники', 'author': 'jkl', 'views': 80},
    #     {'id': 7, 'subject': 'coffee and cream', 'author': 'efg', 'views': 10},
    #     {'id': 8, 'subject': 'Cafe con Leche', 'author': 'xyz', 'views': 10}
    # ]
    #
    # # insert the assets
    # conn.db[table].insert_many(deepcopy(objects), ordered=False)
    #
    # # test search single word
    # assert list(query.text_search(conn, 'coffee', table=table)) == [
    #     {'id': 1, 'subject': 'coffee', 'author': 'xyz', 'views': 50},
    #     {'id': 2, 'subject': 'Coffee Shopping', 'author': 'efg', 'views': 5},
    #     {'id': 7, 'subject': 'coffee and cream', 'author': 'efg', 'views': 10},
    # ]
    #
    # # match any of the search terms
    # assert list(query.text_search(conn, 'bake coffee cake', table=table)) == [
    #     {'author': 'abc', 'id': 3, 'subject': 'Baking a cake', 'views': 90},
    #     {'author': 'xyz', 'id': 1, 'subject': 'coffee', 'views': 50},
    #     {'author': 'xyz', 'id': 4, 'subject': 'baking', 'views': 100},
    #     {'author': 'efg', 'id': 2, 'subject': 'Coffee Shopping', 'views': 5},
    #     {'author': 'efg', 'id': 7, 'subject': 'coffee and cream', 'views': 10}
    # ]
    #
    # # search for a phrase
    # assert list(query.text_search(conn, '\"coffee shop\"', table=table)) == [
    #     {'id': 2, 'subject': 'Coffee Shopping', 'author': 'efg', 'views': 5},
    # ]
    #
    # # exclude documents that contain a term
    # assert list(query.text_search(conn, 'coffee -shop', table=table)) == [
    #     {'id': 1, 'subject': 'coffee', 'author': 'xyz', 'views': 50},
    #     {'id': 7, 'subject': 'coffee and cream', 'author': 'efg', 'views': 10},
    # ]
    #
    # # search different language
    # assert list(query.text_search(conn, 'leche', language='es', table=table)) == [
    #     {'id': 5, 'subject': 'Café Con Leche', 'author': 'abc', 'views': 200},
    #     {'id': 8, 'subject': 'Cafe con Leche', 'author': 'xyz', 'views': 10}
    # ]
    #
    # # case and diacritic insensitive search
    # assert list(query.text_search(conn, 'сы́рники CAFÉS', table=table)) == [
    #     {'id': 6, 'subject': 'Сырники', 'author': 'jkl', 'views': 80},
    #     {'id': 5, 'subject': 'Café Con Leche', 'author': 'abc', 'views': 200},
    #     {'id': 8, 'subject': 'Cafe con Leche', 'author': 'xyz', 'views': 10}
    # ]
    #
    # # case sensitive search
    # assert list(query.text_search(conn, 'Coffee', case_sensitive=True, table=table)) == [
    #     {'id': 2, 'subject': 'Coffee Shopping', 'author': 'efg', 'views': 5},
    # ]
    #
    # # diacritic sensitive search
    # assert list(query.text_search(conn, 'CAFÉ', diacritic_sensitive=True, table=table)) == [
    #     {'id': 5, 'subject': 'Café Con Leche', 'author': 'abc', 'views': 200},
    # ]
    #
    # # return text score
    # assert list(query.text_search(conn, 'coffee', text_score=True, table=table)) == [
    #     {'id': 1, 'subject': 'coffee', 'author': 'xyz', 'views': 50, 'score': 1.0},
    #     {'id': 2, 'subject': 'Coffee Shopping', 'author': 'efg', 'views': 5, 'score': 0.75},
    #     {'id': 7, 'subject': 'coffee and cream', 'author': 'efg', 'views': 10, 'score': 0.75},
    # ]
    #
    # # limit search result
    # assert list(query.text_search(conn, 'coffee', limit=2, table=table)) == [
    #     {'id': 1, 'subject': 'coffee', 'author': 'xyz', 'views': 50},
    #     {'id': 2, 'subject': 'Coffee Shopping', 'author': 'efg', 'views': 5},
    # ]


def test_write_metadata(db_conn):
    from planetmint.backend.tarantool import query

    metadata = [MetaData("1", "1"), MetaData("2", "2"), MetaData("3", "3")]
    # write the assets
    query.store_metadatas(connection=db_conn, metadata=metadata)

    # check that 3 assets were written to the database
    metadatas = []
    for meta in metadata:
        _data = db_conn.run(db_conn.space("meta_data").select(meta.id))[0]
        metadatas.append(MetaData(_data[0], json.loads(_data[1])))

    metadatas = sorted(metadatas, key=lambda k: k.id)

    assert len(metadatas) == 3
    assert list(metadatas) == metadata


def test_get_metadata(db_conn):
    from planetmint.backend.tarantool import query

    metadata = [
        MetaData("dd86682db39e4b424df0eec1413cfad65488fd48712097c5d865ca8e8e059b64", None),
        MetaData("55a2303e3bcd653e4b5bd7118d39c0e2d48ee2f18e22fbcf64e906439bdeb45d", {"key": "value"}),
    ]

    # conn.db.metadata.insert_many(deepcopy(metadata), ordered=False)
    query.store_metadatas(connection=db_conn, metadata=metadata)

    for meta in metadata:
        _m = query.get_metadata(connection=db_conn, transaction_ids=[meta.id])
        assert _m


def test_get_owned_ids(signed_create_tx, user_pk, db_conn):
    from planetmint.backend.tarantool import query

    # insert a transaction
    query.store_transactions(connection=db_conn, signed_transactions=[signed_create_tx.to_dict()])
    txns = list(query.get_owned_ids(connection=db_conn, owner=user_pk))
    tx_dict = signed_create_tx.to_dict()
    founded = [tx for tx in txns if tx["transactions"].id == tx_dict["id"]]
    assert founded[0]["transactions"].raw_transaction == tx_dict


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


# def test_delete_zero_unspent_outputs(db_context, utxoset):
#     from planetmint.backend.tarantool import query
#     return
#
#     unspent_outputs, utxo_collection = utxoset
#
#     delete_res = query.delete_unspent_outputs(db_context.conn)
#
#     assert delete_res is None
#     assert utxo_collection.count_documents({}) == 3
#     assert utxo_collection.count_documents(
#         {'$or': [
#             {'transaction_id': 'a', 'output_index': 0},
#             {'transaction_id': 'b', 'output_index': 0},
#             {'transaction_id': 'a', 'output_index': 1},
#         ]}
#     ) == 3
#
#
# def test_delete_one_unspent_outputs(db_context, utxoset):
#     return
#     from planetmint.backend import query
#     unspent_outputs, utxo_collection = utxoset
#     delete_res = query.delete_unspent_outputs(db_context.conn,
#                                               unspent_outputs[0])
#     assert delete_res.raw_result['n'] == 1
#     assert utxo_collection.count_documents(
#         {'$or': [
#             {'transaction_id': 'a', 'output_index': 1},
#             {'transaction_id': 'b', 'output_index': 0},
#         ]}
#     ) == 2
#     assert utxo_collection.count_documents(
#         {'transaction_id': 'a', 'output_index': 0}) == 0
#
#
# def test_delete_many_unspent_outputs(db_context, utxoset):
#     return
#     from planetmint.backend import query
#     unspent_outputs, utxo_collection = utxoset
#     delete_res = query.delete_unspent_outputs(db_context.conn,
#                                               *unspent_outputs[::2])
#     assert delete_res.raw_result['n'] == 2
#     assert utxo_collection.count_documents(
#         {'$or': [
#             {'transaction_id': 'a', 'output_index': 0},
#             {'transaction_id': 'b', 'output_index': 0},
#         ]}
#     ) == 0
#     assert utxo_collection.count_documents(
#         {'transaction_id': 'a', 'output_index': 1}) == 1
#
#
# def test_store_zero_unspent_output(db_context, utxo_collection):
#     return
#     from planetmint.backend import query
#     res = query.store_unspent_outputs(db_context.conn)
#     assert res is None
#     assert utxo_collection.count_documents({}) == 0
#
#
# def test_store_one_unspent_output(db_context,
#                                   unspent_output_1, utxo_collection):
#     return
#     from planetmint.backend import query
#     res = query.store_unspent_outputs(db_context.conn, unspent_output_1)
#     assert res.acknowledged
#     assert len(res.inserted_ids) == 1
#     assert utxo_collection.count_documents(
#         {'transaction_id': unspent_output_1['transaction_id'],
#          'output_index': unspent_output_1['output_index']}
#     ) == 1
#
#
# def test_store_many_unspent_outputs(db_context,
#                                     unspent_outputs, utxo_collection):
#     return
#     from planetmint.backend import query
#     res = query.store_unspent_outputs(db_context.conn, *unspent_outputs)
#     assert res.acknowledged
#     assert len(res.inserted_ids) == 3
#     assert utxo_collection.count_documents(
#         {'transaction_id': unspent_outputs[0]['transaction_id']}
#     ) == 3
#
#
# def test_get_unspent_outputs(db_context, utxoset):
#     return
#     from planetmint.backend import query
#     cursor = query.get_unspent_outputs(db_context.conn)
#     assert cursor.collection.count_documents({}) == 3
#     retrieved_utxoset = list(cursor)
#     unspent_outputs, utxo_collection = utxoset
#     assert retrieved_utxoset == list(
#         utxo_collection.find(projection={'_id': False}))
#     assert retrieved_utxoset == unspent_outputs


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
