import tarantool
import os
from planetmint.backend.tarantool.utils import run


class TarantoolDB:
    def __init__(self , host , port , username , password):
        self.conn = tarantool.connect(host=host , port=port , user = username , password=password)

    
    def connect_to_sapce(self,spacename):
        self.conn.space(spacename)


def init_tarantool():
    path = os.getcwd()
    run(["mkdir" , "tarantool"])
    run(["ln","-s",path +"/init.lua","init.lua"] , path+"/tarantool")
    run (["tarantool" , "init.lua"] ,path+ "/tarantool")

def drop_tarantool():
    #TODO drop tarantool
    pass