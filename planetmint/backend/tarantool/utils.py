import os
import subprocess




def run(command,path=None,file_name=None):
    config = {
        "login": "admin",
        "host": "admin:pass@127.0.0.1:3301",
        "service": "tarantoolctl connect"
    }
    if file_name is not None:
        file = open(file_name, 'r')
        commands = [line + '\n' for line in file.readlines() if len(str(line)) > 1]
        file.close()
        process = subprocess.Popen(command + config["host"],
                                    stdin=subprocess.PIPE,
                                    stdout=subprocess.PIPE,
                                    universal_newlines=True,
                                    bufsize=0,
                                    shell=True)

        for cmd in commands:
            process.stdin.write(cmd)
        process.stdin.close()

        for line in process.stdout:
            print(line)
            
    if path is not None:
        os.chdir(path)
        process = subprocess.Popen(command,stdin=subprocess.PIPE,
                                    stdout=subprocess.PIPE,
                                    universal_newlines=True,
                                    bufsize=0,
                                    shell=True)
        output ,error = process.communicate()
        if process.returncode != 0:
            print(str(process.returncode) + "\n" + str(output) + "\n" + str(error))

