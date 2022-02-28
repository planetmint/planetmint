# Copyright © 2020 Interplanetary Database Association e.V.,
# Planetmint and IPDB software contributors.
# SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
# Code is Apache-2.0 and docs are CC-BY-4.0

import logging
from importlib import import_module
from itertools import repeat

import tarantool
import planetmint
import os

from planetmint.backend.exceptions import ConnectionError
from planetmint.backend.utils import get_planetmint_config_value, get_planetmint_config_value_or_key_error
from planetmint.common.exceptions import ConfigurationError

BACKENDS = {  # This is path to MongoDBClass
    'tarantool': 'planetmint.backend.connection_tarantool.TarantoolDB',
}

logger = logging.getLogger(__name__)


class TarantoolDB:
    init_config = {
        "init_file": "init_db.txt",
        "relative_path": os.path.dirname(os.path.abspath(__file__)) + "/backend/tarantool/"
    }

    drop_config = {
        "drop_file": "drop_db.txt",  # planetmint/backend/tarantool/init_db.txt
        "relative_path": os.path.dirname(os.path.abspath(__file__)) + "/backend/tarantool/"
    }
    
    def __init__(self, host: str, port: int, user: str, password: str, reset_database: bool = False):
        self.db_connect = tarantool.connect(host=host, port=port, user=user, password=password)
        if reset_database:
            self.drop_database()
            self.init_database()
            test_conn = self.db_connect.space("transactions")

    def get_connection(self, space_name: str = None):
        return self.db_connect if space_name is None else self.db_connect.space(space_name)

    def __read_commands(self, file_path):
        with open(file_path, "r") as cmd_file:
            commands = [line.strip() for line in cmd_file.readlines() if len(str(line)) > 1]
            cmd_file.close()
        return commands

    def drop_database(self):
        from planetmint.backend.tarantool.utils import run
#        config = get_planetmint_config_value_or_key_error("ctl_config")
#        drop_config = config["drop_config"]
        f_path = "%s%s" % (self.drop_config["relative_path"], self.drop_config["drop_file"])
        commands = self.__read_commands(file_path=f_path)
        run(commands=commands, config=config)

    def init_database(self):
        from planetmint.backend.tarantool.utils import run
 #       config = get_planetmint_config_value_or_key_error("ctl_config")
 #       init_config = config["init_config"]
        f_path = "%s%s" % (self.init_config["relative_path"], self.init_config["init_file"])
        commands = self.__read_commands(file_path=f_path)
        run(commands=commands, config=config)



def connect(host: str = None, port: int = None, username: str = None, password: str = None,
            backend: str = None, reset_database: bool = False, name=None, max_tries=None,
            connection_timeout=None, replicaset=None, ssl=None, login: str = None, ctl_config=None,
            ca_cert=None, certfile=None, keyfile=None, keyfile_passphrase=None, reconnect_delay=None,
            crlfile=None, connect_now=True, encoding=None):
    backend = backend or get_planetmint_config_value_or_key_error('backend')  # TODO Rewrite Configs
    host = host or get_planetmint_config_value_or_key_error('host')
    port = port or get_planetmint_config_value_or_key_error('port')
    username = username or login or get_planetmint_config_value('login')
    password = password or get_planetmint_config_value('password')

    try:  # Here we get class using getattr function
        module_name, _, class_name = BACKENDS[backend].rpartition('.')
        Class = getattr(import_module(module_name), class_name)
    except KeyError:
        raise ConfigurationError('Backend `{}` is not supported. '
                                 'Planetmint currently supports {}'.format(backend, BACKENDS.keys()))
    except (ImportError, AttributeError) as exc:
        raise ConfigurationError('Error loading backend `{}`'.format(backend)) from exc
    print(host)
    print(port)
    print(username)
    
    logger.debug('Connection: {}'.format(Class))
    return Class(host=host, port=port, user=username, password=password, reset_database=reset_database)


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
