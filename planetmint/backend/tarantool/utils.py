import subprocess
from planetmint.config import Config


def run(commands: list, config: dict):
    sshProcess = subprocess.Popen(
        ['%s %s:%s@%s:%s' % (config["service"], config["login"], config["password"], config["host"], config["port"])],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        universal_newlines=True,
        bufsize=0,
        shell=True)

    for cmd in commands:
        try:
            sshProcess.stdin.write(cmd)
        except Exception as cmd_err:
            print(str(cmd_err))
    sshProcess.stdin.close()
    #  TODO To add here Exception Handler for stdout
    # for line in sshProcess.stdout:
    #     print(line)


def __read_commands(file_path):
    with open(file_path, "r") as cmd_file:
        commands = [line.strip()+'\n' for line in cmd_file.readlines() if len(str(line)) > 1]
        cmd_file.close()
    return commands


def _load_setup_files():
    drop_commands = __read_commands(file_path="planetmint/backend/tarantool/drop_db.txt")
    init_commands = __read_commands(file_path="planetmint/backend/tarantool/init_db.txt")
    return init_commands, drop_commands


init, drop = _load_setup_files()
db_config = Config().get()["database"]
run(commands=drop, config=db_config)
