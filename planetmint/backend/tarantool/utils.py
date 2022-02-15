import os
import subprocess


def run(command, path=None):
    if path is not None:
        os.chdir(path)
        p = subprocess.Popen(
            command
        )

        # output, error = p.communicate()  # TODO Here was problem that we are waiting for outputs
        # if p.returncode != 0:
        #     print(str(p.returncode) + "\n" + str(output) + "\n" + str(error))
    else:
        p = subprocess.Popen(
            command
        )

        # output, error = p.communicate()
        # if p.returncode != 0:
        #     print(str(p.returncode) + "\n" + str(output) + "\n" + str(error))
