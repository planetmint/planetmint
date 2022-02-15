import tarantool
import os
from planetmint.backend.tarantool.utils import run


def init_tarantool():
    if os.path.exists(os.path.join(os.getcwd(), 'tarantool', 'init.lua')) is not True:
        path = os.getcwd()
        run(["mkdir", "tarantool_snap"])
        run(["ln", "-s", path + "/init.lua", "init.lua"], path + "/tarantool_snap")
        run(["tarantool", "init.lua"], path + "/tarantool")
    else:
        raise Exception("There is a instance of tarantool already created in %s" + os.getcwd() + "/tarantool_snap")


def drop_tarantool():
    if os.path.exists(os.path.join(os.getcwd(), 'tarantool', 'init.lua')) is not True:
        path = os.getcwd()
        run(["ln", "-s", path + "/drop_db.lua", "drop_db.lua"], path + "/tarantool_snap")
        run(["tarantool", "drop_db.lua"])
    else:
        raise Exception("There is no tarantool spaces to drop")


class TarantoolDB:
    def __init__(self, host: str, port: int, username: str, password: str):
        self.db_connect = tarantool.connect(host=host, port=port, user=username, password=password)
        self._spaces = {
            "abci_chains": self.db_connect.space("abci_chains"),
            "assets": self.db_connect.space("assets"),
            "blocks": {"blocks": self.db_connect.space("blocks"), "blocks_tx": self.db_connect.space("blocks_tx")},
            "elections": self.db_connect.space("elections"),
            "meta_data": self.db_connect.space("meta_data"),
            "pre_commits": self.db_connect.space("pre_commits"),
            "validators": self.db_connect.space("validators"),
            "transactions": {
                "transactions": self.db_connect.space("transactions"),
                "inputs": self.db_connect.space("inputs"),
                "outputs": self.db_connect.space("outputs"),
                "keys": self.db_connect.space("keys")
            }
        }

    def get_space(self, spacename: str):
        return self._spaces[spacename]
