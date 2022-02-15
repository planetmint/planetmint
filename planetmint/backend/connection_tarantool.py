# Copyright © 2020 Interplanetary Database Association e.V.,
# Planetmint and IPDB software contributors.
# SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
# Code is Apache-2.0 and docs are CC-BY-4.0

import logging
from importlib import import_module
from itertools import repeat

import tarantool

import os
import pathlib

from planetmint.backend.tarantool.utils import run

import planetmint
from planetmint.backend.exceptions import ConnectionError
from planetmint.backend.utils import get_planetmint_config_value, get_planetmint_config_value_or_key_error
from planetmint.common.exceptions import ConfigurationError

BACKENDS = {  # This is path to MongoDBClass
    'tarantool_db': 'planetmint.backend.connection_tarantool.TarantoolDB',
}

logger = logging.getLogger(__name__)


def init_tarantool():
    init_lua_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tarantool", "init_db.lua")
    tarantool_root = os.path.join(pathlib.Path.home(), 'tarantool')
    snap = os.path.join(pathlib.Path.home(), 'tarantool_snap')
    init_lua = os.path.join(tarantool_root, 'init_db.lua')
    if os.path.exists(tarantool_root) is not True:
        run(["mkdir", tarantool_root])
        # run(["cp", init_lua_path, tarantool_root])
        run(["mkdir", snap])
        # run(["ln", "-s", init_lua, "init.lua"], snap)
        run(["tarantool", init_lua_path], tarantool_root)
    else:
        raise Exception("There is a instance of tarantool already created in %s" + snap)


def drop_tarantool():
    drop_lua_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tarantool", "drop_db.lua")
    tarantool_root = os.path.join(pathlib.Path.home(), 'tarantool')
    snap = os.path.join(pathlib.Path.home(), 'tarantool_snap')
    init_lua = os.path.join(tarantool_root, 'init_db.lua')
    drop_lua = os.path.join(tarantool_root, "/drop_db.lua")
    if os.path.exists(init_lua) is not True:
        # run(["cp", drop_lua_path, tarantool_root])
        # run(["ln", "-s", drop_lua, "drop_db.lua"], snap)
        run(["tarantool", drop_lua_path])
    else:
        raise Exception("There is no tarantool spaces to drop")


class TarantoolDB:
    def __init__(self, host: str, port: int, username: str, password: str):
        init_tarantool()
        self.db_connect = tarantool.connect(host=host, port=port, user=username, password=password)
        self._spaces = {
            "abci_chains": self.db_connect.space("abci_chains"),
            "assets": self.db_connect.space("assets"),
            "blocks": {"blocks": self.db_connect.space("blocks"), "blocks_tx": self.db_connect.space("blocks_tx")},
            "elections": self.db_connect.space("elections"),
            "meta_data": self.db_connect.space("meta_data"),
            "pre_commits": self.db_connect.space("pre_commits"),
            "validators": self.db_connect.space("validators"),
            "transactions": {
                "transactions": self.db_connect.space("transactions"),
                "inputs": self.db_connect.space("inputs"),
                "outputs": self.db_connect.space("outputs"),
                "keys": self.db_connect.space("keys")
            }
        }

    def get_space(self, spacename: str):
        return self._spaces[spacename]


def connect(host: str = None, port: int = None, username: str = "admin", password: str = "pass", backend: str = None):
    """Create a new connection to the database backend.

    All arguments default to the current configuration's values if not
    given.

    Args:
        backend (str): the name of the backend to use.
        host (str): the host to connect to.
        port (int): the port to connect to.

    Returns:
        An instance of :class:`~planetmint.backend.connection.Connection`
        based on the given (or defaulted) :attr:`backend`.

    Raises:
        :exc:`~ConnectionError`: If the connection to the database fails.
        :exc:`~ConfigurationError`: If the given (or defaulted) :attr:`backend`
            is not supported or could not be loaded.
        :exc:`~AuthenticationError`: If there is a OperationFailure due to
            Authentication failure after connecting to the database.
    """

    backend = backend or get_planetmint_config_value_or_key_error('backend')  # TODO Rewrite Configs
    host = host or get_planetmint_config_value_or_key_error('host')
    port = port or get_planetmint_config_value_or_key_error('port')
    username = username or get_planetmint_config_value('login')
    password = password or get_planetmint_config_value('password')

    try:  # Here we get class using getattr function
        module_name, _, class_name = BACKENDS[backend].rpartition('.')
        Class = getattr(import_module(module_name), class_name)
    except KeyError:
        raise ConfigurationError('Backend `{}` is not supported. '
                                 'Planetmint currently supports {}'.format(backend, BACKENDS.keys()))
    except (ImportError, AttributeError) as exc:
        raise ConfigurationError('Error loading backend `{}`'.format(backend)) from exc

    logger.debug('Connection: {}'.format(Class))
    return Class(host=host, port=port, username=username, password=password)


class Connection:
    """Connection class interface.

    All backend implementations should provide a connection class that inherits
    from and implements this class.
    """

    def __init__(self, host=None, port=None, connection_timeout=None, max_tries=None,
                 **kwargs):
        """Create a new :class:`~.Connection` instance.

        Args:
            host (str): the host to connect to.
            port (int): the port to connect to.
            dbname (str): the name of the database to use.
            connection_timeout (int, optional): the milliseconds to wait
                until timing out the database connection attempt.
                Defaults to 5000ms.
            max_tries (int, optional): how many tries before giving up,
                if 0 then try forever. Defaults to 3.
            **kwargs: arbitrary keyword arguments provided by the
                configuration's ``database`` settings
        """

        dbconf = planetmint.config['database']

        self.host = host or dbconf['host']
        self.port = port or dbconf['port']
        self.connection_timeout = connection_timeout if connection_timeout is not None \
            else dbconf['connection_timeout']
        self.max_tries = max_tries if max_tries is not None else dbconf['max_tries']
        self.max_tries_counter = range(self.max_tries) if self.max_tries != 0 else repeat(0)
        self._conn = None

    @property
    def conn(self):
        pass
        if self._conn is None:
            self.connect()
        return self._conn

    def run(self, query):
        pass
        """Run a query.

        Args:
            query: the query to run
        Raises:
            :exc:`~DuplicateKeyError`: If the query fails because of a
                duplicate key constraint.
            :exc:`~OperationFailure`: If the query fails for any other
                reason.
            :exc:`~ConnectionError`: If the connection to the database
                fails.
        """

        raise NotImplementedError()

    def connect(self):
        pass
        """Try to connect to the database.

        Raises:
            :exc:`~ConnectionError`: If the connection to the database
                fails.
        """

        attempt = 0
        for i in self.max_tries_counter:
            attempt += 1
            try:
                self._conn = self._connect()
            except ConnectionError as exc:
                logger.warning('Attempt %s/%s. Connection to %s:%s failed after %sms.',
                               attempt, self.max_tries if self.max_tries != 0 else '∞',
                               self.host, self.port, self.connection_timeout)
                if attempt == self.max_tries:
                    logger.critical('Cannot connect to the Database. Giving up.')
                    raise ConnectionError() from exc
            else:
                break
