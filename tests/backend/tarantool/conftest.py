import pytest
from planetmint.backend.connection import Connection
#
#
#
# @pytest.fixture
# def dummy_db(request):
#     from planetmint.backend import Connection
#
#     conn = Connection()
#     dbname = request.fixturename
#     xdist_suffix = getattr(request.config, 'slaveinput', {}).get('slaveid')
#     if xdist_suffix:
#         dbname = '{}_{}'.format(dbname, xdist_suffix)
#
#     conn.drop_database()
#     #_drop_db(conn, dbname)  # make sure we start with a clean DB
#     #schema.init_database(conn, dbname)
#     conn.init_database()
#     yield dbname
#
#     conn.drop_database()
#     #_drop_db(conn, dbname)

#def _drop_db(conn, dbname):
#    try:
#        conn.drop_database()
#        schema.drop_database(conn, dbname)
#    except DatabaseDoesNotExist:
#        pass

@pytest.fixture
def db_conn():
    conn = Connection()
    return conn
