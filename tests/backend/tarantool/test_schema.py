# Copyright © 2020 Interplanetary Database Association e.V.,
# Planetmint and IPDB software contributors.
# SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
# Code is Apache-2.0 and docs are CC-BY-4.0

from planetmint.backend.tarantool.connection import TarantoolDBConnection


def _check_spaces_by_list(conn, space_names):
    _exists = []
    for name in space_names:
        try:
            conn.get_space(name)
            _exists.append(name)
        except:  # noqa
            pass
    return _exists


def test_create_tables(db_conn):
    db_conn.drop_database()
    db_conn.init_database()
    assert db_conn.SPACE_NAMES == _check_spaces_by_list(conn=db_conn, space_names=db_conn.SPACE_NAMES)


def test_drop(db_conn):  # remove dummy_db as argument
    db_conn.drop_database()
    actual_spaces = _check_spaces_by_list(conn=db_conn, space_names=db_conn.SPACE_NAMES)
    assert [] == actual_spaces
