# Copyright © 2020 Interplanetary Database Association e.V.,
# Planetmint and IPDB software contributors.
# SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
# Code is Apache-2.0 and docs are CC-BY-4.0

import logging
from importlib import import_module
from itertools import repeat

import tarantool

from planetmint.backend.exceptions import ConnectionError
from planetmint.backend.utils import get_planetmint_config_value, get_planetmint_config_value_or_key_error
from planetmint.common.exceptions import ConfigurationError

# BACKENDS = {  # This is path to MongoDBClass
#    'tarantool_db': 'planetmint.backend.connection_tarantool.TarantoolDB',
#    'localmongodb': 'planetmint.backend.localmongodb.connection.LocalMongoDBConnection'
# }

logger = logging.getLogger(__name__)


class TarantoolDB:
    def __init__(self, host: str = "localhost", port: int = 3301, user: str = "guest", password: str = "",
                 reset_database: bool = False):
        self.db_connect = tarantool.connect(host=host, port=port, user=user, password=password)
        if reset_database:
            self.drop_database()
            self.init_database()

    def get_connection(self, space_name: str = None):
        return self.db_connect if space_name is None else self.db_connect.space(space_name)

    def __read_commands(self, file_path):
        with open(file_path, "r") as cmd_file:
            commands = [line.strip() for line in cmd_file.readlines() if len(str(line)) > 1]
            cmd_file.close()
        return commands

    def drop_database(self):
        from planetmint.backend.tarantool.utils import run
        config = get_planetmint_config_value_or_key_error("ctl_config")
        drop_config = config["drop_config"]
        f_path = "%s%s" % (drop_config["relative_path"], drop_config["drop_file"])
        commands = self.__read_commands(file_path=f_path)
        run(commands=commands, config=config)

    def init_database(self):
        from planetmint.backend.tarantool.utils import run
        config = get_planetmint_config_value_or_key_error("ctl_config")
        init_config = config["init_config"]
        f_path = "%s%s" % (init_config["relative_path"], init_config["init_file"])
        commands = self.__read_commands(file_path=f_path)
        run(commands=commands, config=config)
