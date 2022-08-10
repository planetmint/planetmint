# Copyright © 2020 Interplanetary Database Association e.V.,
# Planetmint and IPDB software contributors.
# SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
# Code is Apache-2.0 and docs are CC-BY-4.0

from copy import deepcopy

import pytest
import json
from planetmint.transactions.types.assets.create import Create
from planetmint.transactions.types.assets.transfer import Transfer

pytestmark = pytest.mark.bdb


def test_get_txids_filtered(signed_create_tx, signed_transfer_tx, db_conn):
    from planetmint.backend.tarantool import query
    from planetmint.models import Transaction

    # create and insert two blocks, one for the create and one for the
    # transfer transaction
    create_tx_dict = signed_create_tx.to_dict()
    transfer_tx_dict = signed_transfer_tx.to_dict()

    query.store_transactions(signed_transactions=[create_tx_dict], connection=db_conn)
    query.store_transactions(signed_transactions=[transfer_tx_dict], connection=db_conn)

    asset_id = Transaction.get_asset_id([signed_create_tx, signed_transfer_tx])

    # Test get by just asset id
    txids = set(query.get_txids_filtered(connection=db_conn, asset_id=asset_id))
    assert txids == {signed_create_tx.id, signed_transfer_tx.id}

    # Test get by asset and CREATE
    txids = set(query.get_txids_filtered(connection=db_conn, asset_id=asset_id, operation=Transaction.CREATE))
    assert txids == {signed_create_tx.id}

    # Test get by asset and TRANSFER
    txids = set(query.get_txids_filtered(connection=db_conn, asset_id=asset_id, operation=Transaction.TRANSFER))
    assert txids == {signed_transfer_tx.id}


def test_write_assets(db_conn):
    from planetmint.backend.tarantool import query

    assets = [
        {'id': '1', 'data': '1'},
        {'id': '2', 'data': '2'},
        {'id': '3', 'data': '3'},
        # Duplicated id. Should not be written to the database
        {'id': '1', 'data': '1'},
    ]

    # write the assets
    for asset in assets:
        query.store_asset(connection=db_conn, asset=asset)

    # check that 3 assets were written to the database
    documents = query.get_assets(assets_ids=[asset["id"] for asset in assets], connection=db_conn)

    assert len(documents) == 3
    assert list(documents)[0][0] == assets[:-1][0]


def test_get_assets(db_conn):
    from planetmint.backend import query

    assets = [
        {'id': '1', 'data': '1'},
        {'id': '2', 'data': '2'},
        {'id': '3', 'data': '3'},
    ]

    query.store_assets(assets=deepcopy(assets), connection=db_conn)

    for asset in assets:
        assert query.get_asset(db_conn, asset['id'])


@pytest.mark.skip
@pytest.mark.parametrize('table', ['assets', 'metadata'])
def test_text_search(table):
    from planetmint.backend import connect, query
    conn = connect()

    # function from backend.query.text_search is excpecting only id and data field for assets space.
    # But here we can see multiple fields like: subject, coffe, author, xyz, views...etc.
    objects = [
        {'id': 1, 'subject': 'coffee', 'author': 'xyz', 'views': 50},
        {'id': 2, 'subject': 'Coffee Shopping', 'author': 'efg', 'views': 5},
        {'id': 3, 'subject': 'Baking a cake', 'author': 'abc', 'views': 90},
        {'id': 4, 'subject': 'baking', 'author': 'xyz', 'views': 100},
        {'id': 5, 'subject': 'Café Con Leche', 'author': 'abc', 'views': 200},
        {'id': 6, 'subject': 'Сырники', 'author': 'jkl', 'views': 80},
        {'id': 7, 'subject': 'coffee and cream', 'author': 'efg', 'views': 10},
        {'id': 8, 'subject': 'Cafe con Leche', 'author': 'xyz', 'views': 10}
    ]

    # insert the assets
    conn.db[table].insert_many(deepcopy(objects), ordered=False)

    # test search single word
    assert list(query.text_search(conn, 'coffee', table=table)) == [
        {'id': 1, 'subject': 'coffee', 'author': 'xyz', 'views': 50},
        {'id': 2, 'subject': 'Coffee Shopping', 'author': 'efg', 'views': 5},
        {'id': 7, 'subject': 'coffee and cream', 'author': 'efg', 'views': 10},
    ]

    # match any of the search terms
    assert list(query.text_search(conn, 'bake coffee cake', table=table)) == [
        {'author': 'abc', 'id': 3, 'subject': 'Baking a cake', 'views': 90},
        {'author': 'xyz', 'id': 1, 'subject': 'coffee', 'views': 50},
        {'author': 'xyz', 'id': 4, 'subject': 'baking', 'views': 100},
        {'author': 'efg', 'id': 2, 'subject': 'Coffee Shopping', 'views': 5},
        {'author': 'efg', 'id': 7, 'subject': 'coffee and cream', 'views': 10}
    ]

    # search for a phrase
    assert list(query.text_search(conn, '\"coffee shop\"', table=table)) == [
        {'id': 2, 'subject': 'Coffee Shopping', 'author': 'efg', 'views': 5},
    ]

    # exclude documents that contain a term
    assert list(query.text_search(conn, 'coffee -shop', table=table)) == [
        {'id': 1, 'subject': 'coffee', 'author': 'xyz', 'views': 50},
        {'id': 7, 'subject': 'coffee and cream', 'author': 'efg', 'views': 10},
    ]

    # search different language
    assert list(query.text_search(conn, 'leche', language='es', table=table)) == [
        {'id': 5, 'subject': 'Café Con Leche', 'author': 'abc', 'views': 200},
        {'id': 8, 'subject': 'Cafe con Leche', 'author': 'xyz', 'views': 10}
    ]

    # case and diacritic insensitive search
    assert list(query.text_search(conn, 'сы́рники CAFÉS', table=table)) == [
        {'id': 6, 'subject': 'Сырники', 'author': 'jkl', 'views': 80},
        {'id': 5, 'subject': 'Café Con Leche', 'author': 'abc', 'views': 200},
        {'id': 8, 'subject': 'Cafe con Leche', 'author': 'xyz', 'views': 10}
    ]

    # case sensitive search
    assert list(query.text_search(conn, 'Coffee', case_sensitive=True, table=table)) == [
        {'id': 2, 'subject': 'Coffee Shopping', 'author': 'efg', 'views': 5},
    ]

    # diacritic sensitive search
    assert list(query.text_search(conn, 'CAFÉ', diacritic_sensitive=True, table=table)) == [
        {'id': 5, 'subject': 'Café Con Leche', 'author': 'abc', 'views': 200},
    ]

    # return text score
    assert list(query.text_search(conn, 'coffee', text_score=True, table=table)) == [
        {'id': 1, 'subject': 'coffee', 'author': 'xyz', 'views': 50, 'score': 1.0},
        {'id': 2, 'subject': 'Coffee Shopping', 'author': 'efg', 'views': 5, 'score': 0.75},
        {'id': 7, 'subject': 'coffee and cream', 'author': 'efg', 'views': 10, 'score': 0.75},
    ]

    # limit search result
    assert list(query.text_search(conn, 'coffee', limit=2, table=table)) == [
        {'id': 1, 'subject': 'coffee', 'author': 'xyz', 'views': 50},
        {'id': 2, 'subject': 'Coffee Shopping', 'author': 'efg', 'views': 5},
    ]


def test_write_metadata(db_conn):
    from planetmint.backend import connect, query
    conn = connect()

    metadata = [  # in mongodb implementation 'id' is equal to integer 1, 2 ,3. But in tarantool version we use string
        {'id': '1', 'data': '1'},
        {'id': '2', 'data': '2'},
        {'id': '3', 'data': '3'}
    ]

    # write the assets
    query.store_metadatas(conn, deepcopy(metadata))

    # here we neeed to make query to select all metadatas from space, collection. But instead i search by specific ids.
    # conn.db.metadata.find({}, projection={'_id': False}).sort('id', pymongo.ASCENDING) this is implementation for mongo.
    cursor = query.get_metadata(connection=db_conn, transaction_ids=[meta['id'] for meta in metadata])

    assert len(cursor) == 3  # cursor.collection.count_documents({}) it was like this. Not sure if it will change
    # something, but anyway i mentioned this also.
    assert list(
        cursor) == metadata  # Here we compare two lists, and the problem can be that the order will be different


def test_get_metadata():
    from planetmint.backend import connect, query
    conn = connect()

    metadata = [  # metadata 'id' field was integer now it is string,
        {'id': '1', 'metadata': None},
        {'id': '2', 'metadata': {'key': 'value'}},
        {'id': '3', 'metadata': '3'},
    ]

    conn.db.metadata.insert_many(deepcopy(metadata), ordered=False)

    for meta in metadata:
        assert query.get_metadata(conn, [meta['id']])


def test_get_owned_ids(signed_create_tx, user_pk, db_conn):
    from planetmint.backend.tarantool import query

    # insert a transaction
    query.store_transactions(connection=db_conn, signed_transactions=[signed_create_tx.to_dict()])
    txns = list(query.get_owned_ids(connection=db_conn, owner=user_pk))
    tx_dict = signed_create_tx.to_dict()
    founded = [tx for tx in txns if tx["id"] == tx_dict["id"]]
    assert founded[0] == tx_dict


def test_get_spending_transactions(user_pk, user_sk, db_conn):
    from planetmint.backend.tarantool import query

    out = [([user_pk], 1)]
    tx1 = Create.generate([user_pk], out * 3)
    tx1.sign([user_sk])
    inputs = tx1.to_inputs()
    tx2 = Transfer.generate([inputs[0]], out, tx1.id).sign([user_sk])
    tx3 = Transfer.generate([inputs[1]], out, tx1.id).sign([user_sk])
    tx4 = Transfer.generate([inputs[2]], out, tx1.id).sign([user_sk])
    txns = [deepcopy(tx.to_dict()) for tx in [tx1, tx2, tx3, tx4]]
    query.store_transactions(signed_transactions=txns, connection=db_conn)

    links = [inputs[0].fulfills.to_dict(), inputs[2].fulfills.to_dict()]
    txns = list(query.get_spending_transactions(connection=db_conn, inputs=links))

    # tx3 not a member because input 1 not asked for
    assert txns == [tx2.to_dict(), tx4.to_dict()]


def test_get_spending_transactions_multiple_inputs(db_conn):
    from planetmint.transactions.common.crypto import generate_key_pair
    from planetmint.backend.tarantool import query

    (alice_sk, alice_pk) = generate_key_pair()
    (bob_sk, bob_pk) = generate_key_pair()
    (carol_sk, carol_pk) = generate_key_pair()

    out = [([alice_pk], 9)]
    tx1 = Create.generate([alice_pk], out).sign([alice_sk])

    inputs1 = tx1.to_inputs()
    tx2 = Transfer.generate([inputs1[0]],
                            [([alice_pk], 6), ([bob_pk], 3)],
                            tx1.id).sign([alice_sk])

    inputs2 = tx2.to_inputs()
    tx3 = Transfer.generate([inputs2[0]],
                            [([bob_pk], 3), ([carol_pk], 3)],
                            tx1.id).sign([alice_sk])

    inputs3 = tx3.to_inputs()
    tx4 = Transfer.generate([inputs2[1], inputs3[0]],
                            [([carol_pk], 6)],
                            tx1.id).sign([bob_sk])

    txns = [deepcopy(tx.to_dict()) for tx in [tx1, tx2, tx3, tx4]]
    query.store_transactions(signed_transactions=txns, connection=db_conn)

    links = [
        ({'transaction_id': tx2.id, 'output_index': 0}, 1, [tx3.id]),
        ({'transaction_id': tx2.id, 'output_index': 1}, 1, [tx4.id]),
        ({'transaction_id': tx3.id, 'output_index': 0}, 1, [tx4.id]),
        ({'transaction_id': tx3.id, 'output_index': 1}, 0, None),
    ]
    for li, num, match in links:
        txns = list(query.get_spending_transactions(connection=db_conn, inputs=[li]))
        assert len(txns) == num
        if len(txns):
            assert [tx['id'] for tx in txns] == match


@pytest.mark.skip
def test_store_block(db_conn):
    from planetmint.lib import Block
    from planetmint.backend.tarantool import query
    block = Block(app_hash='random_utxo',
                  height=3,
                  transactions=[])
    query.store_block(connection=db_conn, block=block._asdict())
    # block = query.get_block(connection=db_conn)

    # here we need to select everything from collection or space, but this query will work only with tarantool.
    # We don't have a function that will return everything from collection or space.
    # query.get_block will return you everything from blocks space, but maybe we need more clarity at this kind of moments.
    blocks = db_conn.run(db_conn.space("blocks").select([]))

    assert len(blocks) == 1


@pytest.mark.skip
def test_get_block(db_conn):
    from planetmint.lib import Block
    from planetmint.backend.tarantool import query

    block = Block(app_hash='random_utxo',
                  height=3,
                  transactions=[])

    query.store_block(connection=db_conn, block=block._asdict())

    block = dict(query.get_block(connection=db_conn, block_id=3))  # here we are inserting integer as block_id,
    # but query.get_block is expecting a list with values inside
    assert block['height'] == 3
