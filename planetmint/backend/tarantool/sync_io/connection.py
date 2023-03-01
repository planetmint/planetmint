# Copyright © 2020 Interplanetary Database Association e.V.,
# Planetmint and IPDB software contributors.
# SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
# Code is Apache-2.0 and docs are CC-BY-4.0

import logging
import tarantool


from planetmint.config import Config
from transactions.common.exceptions import ConfigurationError
from planetmint.utils import Lazy
from planetmint.backend.connection import DBConnection
from planetmint.backend.exceptions import ConnectionError

logger = logging.getLogger(__name__)


class TarantoolDBConnection(DBConnection):
    def __init__(
        self,
        host: str = None,
        port: int = None,
        login: str = None,
        password: str = None,
        **kwargs,
    ):
        try:
            super().__init__(host=host, port=port, login=login, password=password, **kwargs)

            dbconf = Config().get()["database"]
            self.init_path = dbconf["init_config"]["absolute_path"]
            self.drop_path = dbconf["drop_config"]["absolute_path"]
            self.__conn = None
            self.connect()
            self.SPACE_NAMES = [
                "abci_chains",
                "blocks",
                "elections",
                "pre_commits",
                "validator_sets",
                "transactions",
                "outputs",
            ]
        except tarantool.error.NetworkError as network_err:
            logger.info("Host cant be reached")
            raise ConnectionError
        except ConfigurationError:
            logger.info("Exception in _connect(): {}")
            raise ConfigurationError

    def query(self):
        return Lazy()

    def _file_content_to_bytes(self, path):
        with open(path, "r") as f:
            execute = f.readlines()
            f.close()
        return "".join(execute).encode(encoding="utf-8")

    def connect(self):
        if not self.__conn:
            self.__conn = tarantool.Connection(
                host=self.host, port=self.port, encoding="utf-8", connect_now=True, reconnect_delay=0.1
            )
        elif self.__conn.connected == False:
            self.__conn.connect()
        return self.__conn

    def close(self):
        try:
            if self.__conn:
                self.__conn.close()
                self.__conn = None
        except Exception as exc:
            logger.info("Exception in planetmint.backend.tarantool.close(): {}".format(exc))
            raise ConnectionError(str(exc)) from exc

    def get_space(self, space_name: str):
        return self.connect().space(space_name)

    def drop_database(self):
        self.connect().call("drop")

    def init_database(self):
        self.connect().call("init")
