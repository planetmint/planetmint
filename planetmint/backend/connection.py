# Copyright © 2020 Interplanetary Database Association e.V.,
# Planetmint and IPDB software contributors.
# SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
# Code is Apache-2.0 and docs are CC-BY-4.0

import logging
from importlib import import_module
from itertools import repeat

import planetmint
from planetmint.backend.exceptions import ConnectionError
from planetmint.backend.utils import get_planetmint_config_value, get_planetmint_config_value_or_key_error
from planetmint.transactions.common.exceptions import ConfigurationError

BACKENDS = {
    'localmongodb': 'planetmint.backend.localmongodb.connection.LocalMongoDBConnection',
}

logger = logging.getLogger(__name__)


def connect(backend=None, host=None, port=None, name=None, max_tries=None,
            connection_timeout=None, replicaset=None, ssl=None, login=None, password=None,
            ca_cert=None, certfile=None, keyfile=None, keyfile_passphrase=None,
            crlfile=None):
    """Create a new connection to the database backend.

    All arguments default to the current configuration's values if not
    given.

    Args:
        backend (str): the name of the backend to use.
        host (str): the host to connect to.
        port (int): the port to connect to.
        name (str): the name of the database to use.
        replicaset (str): the name of the replica set (only relevant for
                          MongoDB connections).

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

    backend = backend or get_planetmint_config_value_or_key_error('backend')
    host = host or get_planetmint_config_value_or_key_error('host')
    port = port or get_planetmint_config_value_or_key_error('port')
    dbname = name or get_planetmint_config_value_or_key_error('name')
    # Not sure how to handle this here. This setting is only relevant for
    # mongodb.
    # I added **kwargs for both RethinkDBConnection and MongoDBConnection
    # to handle these these additional args. In case of RethinkDBConnection
    # it just does not do anything with it.
    #
    # UPD: RethinkDBConnection is not here anymore cause we no longer support RethinkDB.
    # The problem described above might be reconsidered next time we introduce a backend,
    # if it ever happens.
    replicaset = replicaset or get_planetmint_config_value('replicaset')
    ssl = ssl if ssl is not None else get_planetmint_config_value('ssl', False)
    login = login or get_planetmint_config_value('login')
    password = password or get_planetmint_config_value('password')
    ca_cert = ca_cert or get_planetmint_config_value('ca_cert')
    certfile = certfile or get_planetmint_config_value('certfile')
    keyfile = keyfile or get_planetmint_config_value('keyfile')
    keyfile_passphrase = keyfile_passphrase or get_planetmint_config_value('keyfile_passphrase', None)
    crlfile = crlfile or get_planetmint_config_value('crlfile')

    try:
        module_name, _, class_name = BACKENDS[backend].rpartition('.')
        Class = getattr(import_module(module_name), class_name)
    except KeyError:
        raise ConfigurationError('Backend `{}` is not supported. '
                                 'Planetmint currently supports {}'.format(backend, BACKENDS.keys()))
    except (ImportError, AttributeError) as exc:
        raise ConfigurationError('Error loading backend `{}`'.format(backend)) from exc

    logger.debug('Connection: {}'.format(Class))
    return Class(host=host, port=port, dbname=dbname,
                 max_tries=max_tries, connection_timeout=connection_timeout,
                 replicaset=replicaset, ssl=ssl, login=login, password=password,
                 ca_cert=ca_cert, certfile=certfile, keyfile=keyfile,
                 keyfile_passphrase=keyfile_passphrase, crlfile=crlfile)


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

        dbconf = planetmint.config['database']

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
