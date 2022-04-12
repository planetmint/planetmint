# Copyright © 2020 Interplanetary Database Association e.V.,
# Planetmint and IPDB software contributors.
# SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
# Code is Apache-2.0 and docs are CC-BY-4.0

from planetmint.config import Config
from planetmint.backend import Connection
from planetmint.backend.tarantool.connection import TarantoolDB


# This function creates database, we have now only spaces so for now it is commented
# def test_init_database_is_graceful_if_db_exists():
#     conn = TarantoolDB('localhost', 3303)
#     conn.drop_database()
#     conn.init_database()

def _check_spaces_by_list(conn, space_names):
    _exists = []
    for name in space_names:
        try:
            conn.space(name)
            _exists.append(name)
        except:
            pass
    return _exists


def test_create_tables():
    conn = TarantoolDB('localhost', 3303)
    # The db is set up by the fixtures so we need to remove it
    # conn.drop_database()
    conn.init_database()

    assert conn.SPACE_NAMES == _check_spaces_by_list(conn=conn, space_names=conn.SPACE_NAMES)


def test_drop():  # remove dummy_db as argument
    conn = TarantoolDB('localhost', 3303)
    conn.drop_database()
    actual_spaces = _check_spaces_by_list(conn=conn, space_names=conn.SPACE_NAMES)
    assert [] == actual_spaces
