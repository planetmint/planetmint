import warnings

from planetmint.backend.utils import module_dispatch_registrar
from planetmint import backend
from planetmint.backend.tarantool.connection import TarantoolDBConnection

register_schema = module_dispatch_registrar(backend.schema)


@register_schema(TarantoolDBConnection)
def drop_database(connection, not_used=None):
    connection.drop_database()


@register_schema(TarantoolDBConnection)
def create_database(connection, not_used=None):
    connection.init_database()


@register_schema(TarantoolDBConnection)
def create_tables(connection, not_used=None):
    """
    This function is not necessary for using backend tarantool.
    """
    warnings.warn("Function ::create_tables:: Ignored. Not used for create_tables")
