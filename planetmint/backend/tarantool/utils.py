import subprocess


def run_cmd(commands: list, config: dict):
    ret = subprocess.Popen(
        ["%s %s:%s < %s" % ("tarantoolctl connect", "localhost", "3303", "planetmint/backend/tarantool/init.lua")],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        universal_newlines=True,
        bufsize=0,
        shell=True,
    )
    return True if ret >= 0 else False
