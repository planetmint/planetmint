import subprocess


def run(commands: list, config: dict):
    sshProcess = subprocess.Popen(['%s %s' % (config["service"], config["host"])],
                                  stdin=subprocess.PIPE,
                                  stdout=subprocess.PIPE,
                                  universal_newlines=True,
                                  bufsize=0,
                                  shell=True)

    for cmd in commands:
        sshProcess.stdin.write(cmd)
    sshProcess.stdin.close()
    #  TODO To add here Exception Handler for stdout
    # for line in sshProcess.stdout:
    #     print(line)
