from planetmint.backend.utils import module_dispatch_registrar
from planetmint import backend
from planetmint.backend.tarantool.connection import TarantoolDB

register_schema = module_dispatch_registrar(backend.schema)


@register_schema(TarantoolDB)
def drop_database(connection):
    connection.drop_database()
