# Copyright © 2020 Interplanetary Database Association e.V.,
# Planetmint and IPDB software contributors.
# SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
# Code is Apache-2.0 and docs are CC-BY-4.0

import logging
import tarantool

from planetmint.config import Config
from transactions.common.exceptions import ConfigurationError
from planetmint.utils import Lazy
from planetmint.backend.connection import DBConnection, ConnectionError

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
                "scripts",
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
        return "".join(execute).encode()

    def connect(self):
        if not self.__conn:
            self.__conn = tarantool.connect(host=self.host, port=self.port)
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

    def space(self, space_name: str):
        return self.query().space(space_name)

    def exec(self, query, only_data=True):
        try:
            conn = self.connect()
            conn.execute(query) if only_data else conn.execute(query)
        except tarantool.error.OperationalError as op_error:
            raise op_error
        except tarantool.error.NetworkError as net_error:
            raise net_error

    def run(self, query, only_data=True):
        try:
            conn = self.connect()
            return query.run(conn).data if only_data else query.run(conn)
        except tarantool.error.OperationalError as op_error:
            raise op_error
        except tarantool.error.NetworkError as net_error:
            raise net_error

    def drop_database(self):
        db_config = Config().get()["database"]
        cmd_resp = self.run_command(command=self.drop_path, config=db_config)  # noqa: F841

    def init_database(self):
        db_config = Config().get()["database"]
        cmd_resp = self.run_command(command=self.init_path, config=db_config)  # noqa: F841

    def run_command(self, command: str, config: dict):
        from subprocess import run

        try:
            self.close()
        except ConnectionError:
            pass

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

    def run_command_with_output(self, command: str):
        from subprocess import run

        try:
            self.close()
        except ConnectionError:
            pass

        host_port = "%s:%s" % (
            Config().get()["database"]["host"],
            Config().get()["database"]["port"],
        )
        output = run(["tarantoolctl", "connect", host_port], input=command, capture_output=True)
        if output.returncode != 0:
            raise Exception(f"Error while trying to execute cmd {command} on host:port {host_port}: {output.stderr}")
        return output.stdout
