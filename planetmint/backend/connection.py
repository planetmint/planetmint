# Copyright © 2020 Interplanetary Database Association e.V.,
# Planetmint and IPDB software contributors.
# SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
# Code is Apache-2.0 and docs are CC-BY-4.0

import logging

from itertools import repeat
from importlib import import_module
from transactions.common.exceptions import ConfigurationError
from planetmint.config import Config

BACKENDS = {
    "tarantool_db": "planetmint.backend.tarantool.sync_io.connection.TarantoolDBConnection",
    "localmongodb": "planetmint.backend.localmongodb.connection.LocalMongoDBConnection",
}

logger = logging.getLogger(__name__)


def _kwargs_parser(key, kwargs):
    if kwargs.get(key):
        return kwargs[key]
    return None


class DBSingleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            try:
                backend = kwargs.get("backend") if kwargs and kwargs.get("backend") else None
                if backend is not None and backend != Config().get()["database"]["backend"]:
                    Config().init_config(backend)
                else:
                    backend = Config().get()["database"]["backend"]
            except KeyError:
                logger.info("Backend {} not supported".format(backend))
                raise ConfigurationError
            modulepath, _, class_name = BACKENDS[backend].rpartition(".")
            Class = getattr(import_module(modulepath), class_name)
            cls._instances[cls] = super(DBSingleton, Class).__call__(*args, **kwargs)
        return cls._instances[cls]


class Connection(metaclass=DBSingleton):
    def __init__(self) -> None:
        pass


class DBConnection(metaclass=DBSingleton):
    """Connection class interface.
    All backend implementations should provide a connection class that inherits
    from and implements this class.
    """

    def __init__(
        self,
        host: str = None,
        port: int = None,
        login: str = None,
        password: str = None,
        backend: str = None,
        connection_timeout: int = None,
        max_tries: int = None,
        async_io: bool = False,
        **kwargs
    ):
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
        dbconf = Config().get()["database"]

        self.host = host or dbconf["host"] if not kwargs.get("host") else kwargs["host"]
        self.port = port or dbconf["port"] if not kwargs.get("port") else kwargs["port"]
        self.login = login or dbconf["login"] if not kwargs.get("login") else kwargs["login"]
        self.password = password or dbconf["password"] if not kwargs.get("password") else kwargs["password"]

        self.connection_timeout = connection_timeout if connection_timeout is not None else Config().get()["database"]
        self.max_tries = max_tries if max_tries is not None else dbconf["max_tries"]
        self.max_tries_counter = range(self.max_tries) if self.max_tries != 0 else repeat(0)

    def run(self, query):
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
        """Try to connect to the database.
        Raises:
            :exc:`~ConnectionError`: If the connection to the database
                fails.
        """
        raise NotImplementedError()

    def close(self):
        """Try to close connection to the database.
        Raises:
            :exc:`~ConnectionError`: If the connection to the database
                fails.
        """
        raise NotImplementedError()
