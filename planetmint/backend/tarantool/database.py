import tarantool
import os
from planetmint.backend.tarantool.utils import run


class TarantoolDB:
    def __init__(self, host, port, username, password):
        self.conn = tarantool.connect(host=host, port=port, user=username, password=password)

    def connect_to_sapce(self, spacename):
        self.conn.space(spacename)


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
