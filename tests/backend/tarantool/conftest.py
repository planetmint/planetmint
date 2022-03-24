import pytest
from planetmint.backend import connection


@pytest.fixture
def db_conn():
    conn = connection.Connection()
    return conn
