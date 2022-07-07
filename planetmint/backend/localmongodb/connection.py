# Copyright © 2020 Interplanetary Database Association e.V.,
# Planetmint and IPDB software contributors.
# SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
# Code is Apache-2.0 and docs are CC-BY-4.0

import logging
from ssl import CERT_REQUIRED
import pymongo

from planetmint.config import Config
from planetmint.backend.exceptions import (DuplicateKeyError,
                                           OperationError,
                                           ConnectionError)
from planetmint.transactions.common.exceptions import ConfigurationError
from planetmint.utils import Lazy
from planetmint.backend.connection import Connection

logger = logging.getLogger(__name__)

class LocalMongoDBConnection(Connection):

    def __init__(self, replicaset=None, ssl=None, login=None, password=None,
                 ca_cert=None, certfile=None, keyfile=None,
                 keyfile_passphrase=None, crlfile=None, **kwargs):
        """Create a new Connection instance.

        Args:
            replicaset (str, optional): the name of the replica set to
                                        connect to.
            **kwargs: arbitrary keyword arguments provided by the
                configuration's ``database`` settings
        """

        super().__init__(**kwargs)
        self.replicaset = replicaset or Config().get()['database']['replicaset']
        self.ssl = ssl if ssl is not None else Config().get()['database']['ssl']
        self.login = login or Config().get()['database']['login']
        self.password = password or Config().get()['database']['password']
        self.ca_cert = ca_cert or Config().get()['database']['ca_cert']
        self.certfile = certfile or Config().get()['database']['certfile']
        self.keyfile = keyfile or Config().get()['database']['keyfile']
        self.keyfile_passphrase = keyfile_passphrase or Config().get()['database']['keyfile_passphrase']
        self.crlfile = crlfile or Config().get()['database']['crlfile']
        if not self.ssl:
            self.ssl = False
        if not self.keyfile_passphrase:
            self.keyfile_passphrase = None

    @property
    def db(self):
        return self.conn[self.dbname]

    def query(self):
        return Lazy()

    def collection(self, name):
        """Return a lazy object that can be used to compose a query.

        Args:
            name (str): the name of the collection to query.
        """
        return self.query()[self.dbname][name]

    def run(self, query):
        try:
            try:
                return query.run(self.conn)
            except pymongo.errors.AutoReconnect:
                logger.warning('Lost connection to the database, '
                               'retrying query.')
                return query.run(self.conn)
        except pymongo.errors.AutoReconnect as exc:
            raise ConnectionError from exc
        except pymongo.errors.DuplicateKeyError as exc:
            raise DuplicateKeyError from exc
        except pymongo.errors.OperationFailure as exc:
            print(f'DETAILS: {exc.details}')
            raise OperationError from exc

    def _connect(self):
        """Try to connect to the database.

        Raises:
            :exc:`~ConnectionError`: If the connection to the database
                fails.
            :exc:`~AuthenticationError`: If there is a OperationFailure due to
                Authentication failure after connecting to the database.
            :exc:`~ConfigurationError`: If there is a ConfigurationError while
                connecting to the database.
        """

        try:
            # FYI: the connection process might raise a
            # `ServerSelectionTimeoutError`, that is a subclass of
            # `ConnectionFailure`.
            # The presence of ca_cert, certfile, keyfile, crlfile implies the
            # use of certificates for TLS connectivity.
            if self.ca_cert is None or self.certfile is None or \
                    self.keyfile is None or self.crlfile is None:
                client = pymongo.MongoClient(self.host,
                                             self.port,
                                             replicaset=self.replicaset,
                                             serverselectiontimeoutms=self.connection_timeout,
                                             ssl=self.ssl,
                                             **MONGO_OPTS)
                if self.login is not None and self.password is not None:
                    client[self.dbname].authenticate(self.login, self.password)
            else:
                logger.info('Connecting to MongoDB over TLS/SSL...')
                client = pymongo.MongoClient(self.host,
                                             self.port,
                                             replicaset=self.replicaset,
                                             serverselectiontimeoutms=self.connection_timeout,
                                             ssl=self.ssl,
                                             ssl_ca_certs=self.ca_cert,
                                             ssl_certfile=self.certfile,
                                             ssl_keyfile=self.keyfile,
                                             ssl_pem_passphrase=self.keyfile_passphrase,
                                             ssl_crlfile=self.crlfile,
                                             ssl_cert_reqs=CERT_REQUIRED,
                                             **MONGO_OPTS)
                if self.login is not None:
                    client[self.dbname].authenticate(self.login,
                                                     mechanism='MONGODB-X509')

            return client

        except (pymongo.errors.ConnectionFailure,
                pymongo.errors.OperationFailure) as exc:
            logger.info('Exception in _connect(): {}'.format(exc))
            raise ConnectionError(str(exc)) from exc
        except pymongo.errors.ConfigurationError as exc:
            raise ConfigurationError from exc


MONGO_OPTS = {
    'socketTimeoutMS': 20000,
}
