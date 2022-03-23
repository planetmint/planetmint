import pytest
from planetmint.backend import connection


@pytest.fixture
def db_conn():
    conn = connection.Connection(backend="tarantool_db")
    return conn
