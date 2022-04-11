# Copyright © 2020 Interplanetary Database Association e.V.,
# Planetmint and IPDB software contributors.
# SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
# Code is Apache-2.0 and docs are CC-BY-4.0

from planetmint.config import Config
from planetmint.backend import Connection
from planetmint.backend.tarantool.connection import TarantoolDB


def test_init_database_is_graceful_if_db_exists():
    conn = TarantoolDB('localhost', 3303)
    conn.drop_database()
    conn.init_database()


def test_create_tables():
    from planetmint.backend import schema

    conn = TarantoolDB('localhost', 3303)
    # conn = Connection()
    # dbname = Config().get()['database']['name']

    # The db is set up by the fixtures so we need to remove it
    conn.drop_database()
    conn.init_database()

    # TOTO verify spaces
    # collection_names = conn.conn[dbname].list_collection_names()
    # assert set(collection_names) == {
    #    'transactions', 'assets', 'metadata', 'blocks', 'utxos', 'validators', 'elections',
    #    'pre_commit', 'abci_chains',
    # }


#
# indexes = conn.conn[dbname]['assets'].index_information().keys()
# assert set(indexes) == {'_id_', 'asset_id', 'text'}
#
# index_info = conn.conn[dbname]['transactions'].index_information()
# indexes = index_info.keys()
# assert set(indexes) == {
#    '_id_', 'transaction_id', 'asset_id', 'outputs', 'inputs'}
# assert index_info['transaction_id']['unique']
#
# index_info = conn.conn[dbname]['blocks'].index_information()
# indexes = index_info.keys()
# assert set(indexes) == {'_id_', 'height'}
# assert index_info['height']['unique']
#
# index_info = conn.conn[dbname]['utxos'].index_information()
# assert set(index_info.keys()) == {'_id_', 'utxo'}
# assert index_info['utxo']['unique']
# assert index_info['utxo']['key'] == [('transaction_id', 1),
#                                     ('output_index', 1)]
#
# indexes = conn.conn[dbname]['elections'].index_information()
# assert set(indexes.keys()) == {'_id_', 'election_id_height'}
# assert indexes['election_id_height']['unique']
#
# indexes = conn.conn[dbname]['pre_commit'].index_information()
# assert set(indexes.keys()) == {'_id_', 'height'}
# assert indexes['height']['unique']

def _check_spaces_by_list(conn, space_names):
    _exists = []
    for name in space_names:
        try:
            conn.space(name)
            _exists.append(name)
        except:
            pass
    return _exists


def test_drop():  # remove dummy_db as argument
    conn = TarantoolDB('localhost', 3303)
    conn.drop_database()
    actual_spaces = _check_spaces_by_list(conn=conn, space_names=conn.SPACE_NAMES)
    assert [] == actual_spaces
    # conn.init_database()
    # actual_spaces1 = _check_spaces_by_list(conn=conn, space_names=conn.SPACE_NAMES)
    # assert conn.SPACE_NAMES == actual_spaces1
