# Copyright © 2020 Interplanetary Database Association e.V.,
# Planetmint and IPDB software contributors.
# SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
# Code is Apache-2.0 and docs are CC-BY-4.0

import logging
from ssl import CERT_REQUIRED
import pymongo

from planetmint.config import Config
from planetmint.backend.exceptions import DuplicateKeyError, OperationError, ConnectionError
from transactions.common.exceptions import ConfigurationError
from planetmint.utils import Lazy
from planetmint.backend.connection import DBConnection, _kwargs_parser

logger = logging.getLogger(__name__)


class LocalMongoDBConnection(DBConnection):
    def __init__(self, host: str = None, port: int = None, login: str = None, password: str = None, **kwargs):
        """Create a new Connection instance.

        Args:
            replicaset (str, optional): the name of the replica set to
                                        connect to.
            **kwargs: arbitrary keyword arguments provided by the
                configuration's ``database`` settings
        """

        super().__init__(host=host, port=port, login=login, password=password, **kwargs)

        dbconf = Config().get()["database"]
        self.dbname = _kwargs_parser(key="name", kwargs=kwargs) or dbconf["name"]
        self.replicaset = _kwargs_parser(key="replicaset", kwargs=kwargs) or dbconf["replicaset"]
        self.ssl = _kwargs_parser(key="ssl", kwargs=kwargs) or dbconf["ssl"]

        self.ca_cert = _kwargs_parser(key="ca_cert", kwargs=kwargs) or dbconf["ca_cert"]
        self.certfile = _kwargs_parser(key="certfile", kwargs=kwargs) or dbconf["certfile"]
        self.keyfile = _kwargs_parser(key="keyfile", kwargs=kwargs) or dbconf["keyfile"]
        self.keyfile_passphrase = (
            _kwargs_parser(key="keyfile_passphrase", kwargs=kwargs) or dbconf["keyfile_passphrase"]
        )
        self.crlfile = _kwargs_parser(key="crlfile", kwargs=kwargs) or dbconf["crlfile"]
        self.max_tries = _kwargs_parser(key="max_tries", kwargs=kwargs)
        self.connection_timeout = (
            _kwargs_parser(key="connection_timeout", kwargs=kwargs) or dbconf["connection_timeout"]
        )
        self.__conn = None
        self.connect()

        if not self.ssl:
            self.ssl = False
        if not self.keyfile_passphrase:
            self.keyfile_passphrase = None

    @property
    def db(self):
        return self.connect()[self.dbname]

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
                return query.run(self.connect())
            except pymongo.errors.AutoReconnect:
                logger.warning("Lost connection to the database, " "retrying query.")
                return query.run(self.connect())
        except pymongo.errors.AutoReconnect as exc:
            raise ConnectionError from exc
        except pymongo.errors.DuplicateKeyError as exc:
            raise DuplicateKeyError from exc
        except pymongo.errors.OperationFailure as exc:
            print(f"DETAILS: {exc.details}")
            raise OperationError from exc

    def connect(self):
        """Try to connect to the database.

        Raises:
            :exc:`~ConnectionError`: If the connection to the database
                fails.
            :exc:`~AuthenticationError`: If there is a OperationFailure due to
                Authentication failure after connecting to the database.
            :exc:`~ConfigurationError`: If there is a ConfigurationError while
                connecting to the database.
        """
        if self.__conn:
            return self.__conn
        try:
            # FYI: the connection process might raise a
            # `ServerSelectionTimeoutError`, that is a subclass of
            # `ConnectionFailure`.
            # The presence of ca_cert, certfile, keyfile, crlfile implies the
            # use of certificates for TLS connectivity.
            if self.ca_cert is None or self.certfile is None or self.keyfile is None or self.crlfile is None:
                client = pymongo.MongoClient(
                    self.host,
                    self.port,
                    replicaset=self.replicaset,
                    serverselectiontimeoutms=self.connection_timeout,
                    ssl=self.ssl,
                    **MONGO_OPTS,
                )
                if self.login is not None and self.password is not None:
                    client[self.dbname].authenticate(self.login, self.password)
            else:
                logger.info("Connecting to MongoDB over TLS/SSL...")
                client = pymongo.MongoClient(
                    self.host,
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
                    **MONGO_OPTS,
                )
                if self.login is not None:
                    client[self.dbname].authenticate(self.login, mechanism="MONGODB-X509")
            self.__conn = client
            return client

        except (pymongo.errors.ConnectionFailure, pymongo.errors.OperationFailure) as exc:
            logger.info("Exception in connect(): {}".format(exc))
            raise ConnectionError(str(exc)) from exc
        except pymongo.errors.ConfigurationError as exc:
            raise ConfigurationError from exc

    def close(self):
        try:
            self.__conn.close()
            self.__conn = None
        except Exception as exc:
            logger.info("Exception in planetmint.backend.localmongodb.close(): {}".format(exc))
            raise ConnectionError(str(exc)) from exc


MONGO_OPTS = {
    "socketTimeoutMS": 20000,
}
