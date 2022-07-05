# Copyright © 2020 Interplanetary Database Association e.V.,
# Planetmint and IPDB software contributors.
# SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
# Code is Apache-2.0 and docs are CC-BY-4.0

from itertools import repeat
import logging
from importlib import import_module

import tarantool

from planetmint.config import Config
from planetmint.backend.exceptions import ConnectionError
from planetmint.transactions.common.exceptions import ConfigurationError

BACKENDS = {
    'tarantool_db': 'planetmint.backend.tarantool.connection.TarantoolDBConnection',
    'localmongodb': 'planetmint.backend.localmongodb.connection.LocalMongoDBConnection'
}

logger = logging.getLogger(__name__)


def connect(host: str = None, port: int = None, login: str = None, password: str = None, backend: str = None,
               **kwargs):
    try:
        backend = backend
        if not backend and kwargs and kwargs.get("backend"):
            backend = kwargs["backend"]

        if backend and backend != Config().get()["database"]["backend"]:
            Config().init_config(backend)
        else:
            backend = Config().get()["database"]["backend"]
    except KeyError:
        logger.info("Backend {} not supported".format(backend))
        raise ConfigurationError

    host = host or Config().get()["database"]["host"] if not kwargs.get("host") else kwargs["host"]
    port = port or Config().get()['database']['port'] if not kwargs.get("port") else kwargs["port"]
    login = login or Config().get()["database"]["login"] if not kwargs.get("login") else kwargs["login"]
    password = password or Config().get()["database"]["password"]
    try:
        if backend == "tarantool_db":
            modulepath, _, class_name = BACKENDS[backend].rpartition('.')
            Class = getattr(import_module(modulepath), class_name)
            return Class(host=host, port=port, user=login, password=password, kwargs=kwargs)
        elif backend == "localmongodb":
            modulepath, _, class_name = BACKENDS[backend].rpartition('.')
            Class = getattr(import_module(modulepath), class_name)
            dbname = _kwargs_parser(key="name", kwargs=kwargs) or Config().get()['database']['name']
            replicaset = _kwargs_parser(key="replicaset", kwargs=kwargs) or Config().get()['database']['replicaset']
            ssl = _kwargs_parser(key="ssl", kwargs=kwargs) or Config().get()['database']['ssl']
            login = login or Config().get()['database']['login'] if _kwargs_parser(key="login",
                                                                                   kwargs=kwargs) is None else _kwargs_parser(  # noqa: E501
                key="login", kwargs=kwargs)
            password = password or Config().get()['database']['password'] if _kwargs_parser(key="password",
                                                                                            kwargs=kwargs) is None else _kwargs_parser(  # noqa: E501
                key="password", kwargs=kwargs)
            ca_cert = _kwargs_parser(key="ca_cert", kwargs=kwargs) or Config().get()['database']['ca_cert']
            certfile = _kwargs_parser(key="certfile", kwargs=kwargs) or Config().get()['database']['certfile']
            keyfile = _kwargs_parser(key="keyfile", kwargs=kwargs) or Config().get()['database']['keyfile']
            keyfile_passphrase = _kwargs_parser(key="keyfile_passphrase", kwargs=kwargs) or Config().get()['database'][
                'keyfile_passphrase']
            crlfile = _kwargs_parser(key="crlfile", kwargs=kwargs) or Config().get()['database']['crlfile']
            max_tries = _kwargs_parser(key="max_tries", kwargs=kwargs)
            connection_timeout = _kwargs_parser(key="connection_timeout", kwargs=kwargs)

            return Class(host=host, port=port, dbname=dbname,
                         max_tries=max_tries, connection_timeout=connection_timeout,
                         replicaset=replicaset, ssl=ssl, login=login, password=password,
                         ca_cert=ca_cert, certfile=certfile, keyfile=keyfile,
                         keyfile_passphrase=keyfile_passphrase, crlfile=crlfile)
    except tarantool.error.NetworkError as network_err:
        print(f"Host {host}:{port} can't be reached.\n{network_err}")
        raise network_err


def _kwargs_parser(key, kwargs):
    if kwargs.get(key):
        return kwargs[key]
    return None

class Connection:
    """Connection class interface.
    All backend implementations should provide a connection class that inherits
    from and implements this class.
    """

    def __init__(self, host=None, port=None, dbname=None,
                 connection_timeout=None, max_tries=None,
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

        dbconf = Config().get()['database']

        self.host = host or dbconf['host']
        self.port = port or dbconf['port']
        self.dbname = dbname or dbconf['name']
        self.connection_timeout = connection_timeout if connection_timeout is not None \
            else dbconf['connection_timeout']
        self.max_tries = max_tries if max_tries is not None else dbconf['max_tries']
        self.max_tries_counter = range(self.max_tries) if self.max_tries != 0 else repeat(0)
        self._conn = None

    @property
    def conn(self):
        if self._conn is None:
            self.connect()
        return self._conn

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
