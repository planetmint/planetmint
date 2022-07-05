# Copyright © 2020 Interplanetary Database Association e.V.,
# Planetmint and IPDB software contributors.
# SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
# Code is Apache-2.0 and docs are CC-BY-4.0

import logging
import tarantool

from planetmint.config import Config
from planetmint.transactions.common.exceptions import ConfigurationError
from planetmint.utils import Lazy
from planetmint.backend.connection import Connection

logger = logging.getLogger(__name__)


class TarantoolDBConnection(Connection):
    def __init__(
        self,
        host: str = "localhost",
        port: int = 3303,
        user: str = None,
        password: str = None,
        **kwargs,
    ):
        try:
            super().__init__(**kwargs)
            self.host = host
            self.port = port
            # TODO add user support later on
            self.init_path = Config().get()["database"]["init_config"]["absolute_path"]
            self.drop_path = Config().get()["database"]["drop_config"]["absolute_path"]
            self.SPACE_NAMES = [
                "abci_chains",
                "assets",
                "blocks",
                "blocks_tx",
                "elections",
                "meta_data",
                "pre_commits",
                "validators",
                "transactions",
                "inputs",
                "outputs",
                "keys",
            ]
        except tarantool.error.NetworkError as network_err:
            logger.info("Host cant be reached")
            raise network_err
        except ConfigurationError:
            logger.info("Exception in _connect(): {}")
            raise ConfigurationError

    def query(self):
        return Lazy()

    def _file_content_to_bytes(self, path):
        with open(path, "r") as f:
            execute = f.readlines()
            f.close()
        return "".join(execute).encode()

    def _connect(self):
        return tarantool.connect(host=self.host, port=self.port)

    def get_space(self, space_name: str):
        return self.conn.space(space_name)

    def space(self, space_name: str):
        return self.query().space(space_name)

    def run(self, query, only_data=True):
        try:
            return query.run(self.conn).data if only_data else query.run(self.conn)
        except tarantool.error.OperationalError as op_error:
            raise op_error
        except tarantool.error.NetworkError as net_error:
            raise net_error

    def get_connection(self):
        return self.conn

    def drop_database(self):
        db_config = Config().get()["database"]
        cmd_resp = self.run_command(command=self.drop_path, config=db_config)  # noqa: F841

    def init_database(self):
        db_config = Config().get()["database"]
        cmd_resp = self.run_command(command=self.init_path, config=db_config)  # noqa: F841

    def run_command(self, command: str, config: dict):
        from subprocess import run

        print(f" commands: {command}")
        host_port = "%s:%s" % (self.host, self.port)
        execute_cmd = self._file_content_to_bytes(path=command)
        output = run(
            ["tarantoolctl", "connect", host_port],
            input=execute_cmd,
            capture_output=True,
        ).stderr
        output = output.decode()
        return output
