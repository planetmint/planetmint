# Copyright © 2020 Interplanetary Database Association e.V.,
# Planetmint and IPDB software contributors.
# SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
# Code is Apache-2.0 and docs are CC-BY-4.0

import logging

import tarantool
from planetmint.config import Config

logger = logging.getLogger(__name__)


class TarantoolDB:
    def __init__(self, host: str = None, port: int = None, user: str = None, password: str = None,
                 reset_database: bool = False):
        self.host = host
        self.port = port
        self.db_connect = tarantool.connect(host=host, port=port, user=user, password=password)
        self._load_setup_files()
        if reset_database:
            self.drop_database()
            self.init_database()

    def _load_setup_files(self):
        init_path = Config().get()["database"]["init_config"]["absolute_path"]
        drop_path = Config().get()["database"]["drop_config"]["absolute_path"]
        self.drop_commands = self.__read_commands(file_path=init_path)
        self.init_commands = self.__read_commands(file_path=drop_path)

    def space(self, space_name: str):
        return self.db_connect.space(space_name)

    def get_connection(self):
        return self.db_connect

    def __read_commands(self, file_path):
        with open(file_path, "r") as cmd_file:
            commands = [line.strip() for line in cmd_file.readlines() if len(str(line)) > 1]
            cmd_file.close()
        return commands

    def drop_database(self):
        from planetmint.backend.tarantool.utils import run
        db_config = Config().get()["database"]
        # drop_config = db_config["drop_config"]
        # f_path = "%s%s" % (drop_config["relative_path"], drop_config["drop_file"])
        # commands = self.__read_commands(file_path=f_path)
        run(commands=self.drop_commands, config=db_config)

    def init_database(self):
        from planetmint.backend.tarantool.utils import run
        db_config = Config().get()["database"]
        # init_config = db_config["init_config"]
        # f_path = "%s%s" % (init_config["relative_path"], init_config["init_file"])
        # commands = self.__read_commands(file_path=f_path)
        run(commands=self.init_commands, config=db_config)
