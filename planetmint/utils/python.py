import sys


def is_above_py39():
    if sys.version_info.major == 3:
        if sys.version_info.minor < 10:
            return False
        else:
            return True
    elif sys.version_info.major > 3:
        return True
    else:
        return False
