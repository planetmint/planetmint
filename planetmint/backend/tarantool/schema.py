import logging

from planetmint.config import Config
from planetmint.backend.utils import module_dispatch_registrar
from planetmint import backend
from planetmint.backend.tarantool.connection import TarantoolDBConnection

logger = logging.getLogger(__name__)
register_schema = module_dispatch_registrar(backend.schema)


@register_schema(TarantoolDBConnection)
def init_database(connection, db_name=None):
    print("init database tarantool schema")
    connection.connect().call("init")


@register_schema(TarantoolDBConnection)
def drop_database(connection, db_name=None):
    print("drop database tarantool schema")
    connection.connect().call("drop")


@register_schema(TarantoolDBConnection)
def create_database(connection, dbname):
    """

    For tarantool implementation, this function runs
    create_tables, to initiate spaces, schema and indexes.

    """
    logger.info("Create database `%s`.", dbname)


def run_command_with_output(command):
    from subprocess import run

    host_port = "%s:%s" % (
        Config().get()["database"]["host"],
        Config().get()["database"]["port"],
    )
    output = run(["tarantoolctl", "connect", host_port], input=command, capture_output=True)
    if output.returncode != 0:
        raise Exception(f"Error while trying to execute cmd {command} on host:port {host_port}: {output.stderr}")
    return output.stdout


@register_schema(TarantoolDBConnection)
def create_tables(connection, dbname):
    connection.connect().call("init")
