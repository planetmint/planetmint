import copy
import logging
import os
from decouple import config

from planetmint.utils import Singleton
from planetmint.version import __version__


class Config(metaclass=Singleton):
    def __init__(self):
        # from functools import reduce
        # PORT_NUMBER = reduce(lambda x, y: x * y, map(ord, 'Planetmint')) % 2**16
        # basically, the port number is 9984

        # The following variable is used by `planetmint configure` to
        # prompt the user for database values. We cannot rely on
        # _base_database_localmongodb.keys() because dicts are unordered.
        # I tried to configure
        self.log_config = DEFAULT_LOGGING_CONFIG
        db = config("PLANETMINT_DATABASE_BACKEND", default="tarantool_db")
        self.__private_database_keys_map = {  # TODO Check if it is working after removing 'name' field
            "tarantool_db": ("host", "port"),
            "localmongodb": ("host", "port", "name"),
        }
        self.__private_database_localmongodb = {
            "backend": "localmongodb",
            "host": "localhost",
            "port": 27017,
            "name": "bigchain",
            "replicaset": None,
            "login": None,
            "password": None,
            "connection_timeout": 5000,
            "max_tries": 3,
            "ssl": False,
            "ca_cert": None,
            "certfile": None,
            "keyfile": None,
            "keyfile_passphrase": None,
            "crlfile": None,
        }
        self.__private_init_config = {
            "absolute_path": os.path.dirname(os.path.abspath(__file__)) + "/backend/tarantool/init.lua"
        }

        self.__private_drop_config = {
            "absolute_path": os.path.dirname(os.path.abspath(__file__)) + "/backend/tarantool/drop.lua"
        }
        self.__private_database_tarantool = {
            "backend": "tarantool_db",
            "connection_timeout": 5000,
            "max_tries": 3,
            "name": "universe",
            "reconnect_delay": 0.5,
            "host": "localhost",
            "port": 3303,
            "connect_now": True,
            "encoding": "utf-8",
            "login": "guest",
            "password": "",
            "service": "tarantoolctl connect",
            "init_config": self.__private_init_config,
            "drop_config": self.__private_drop_config,
        }

        self.__private_database_map = {
            "tarantool_db": self.__private_database_tarantool,
            "localmongodb": self.__private_database_localmongodb,
        }
        self.__private_config = {
            "server": {
                # Note: this section supports all the Gunicorn settings:
                #       - http://docs.gunicorn.org/en/stable/settings.html
                "bind": "localhost:9984",
                "loglevel": logging.getLevelName(self.log_config["handlers"]["console"]["level"]).lower(),
                "workers": None,  # if None, the value will be cpu_count * 2 + 1
            },
            "wsserver": {
                "scheme": "ws",
                "host": "localhost",
                "port": 9985,
                "advertised_scheme": "ws",
                "advertised_host": "localhost",
                "advertised_port": 9985,
            },
            "tendermint": {
                "host": "localhost",
                "port": 26657,
                "version": "v0.34.15",  # look for __tm_supported_versions__
            },
            "database": self.__private_database_map,
            "log": {
                "file": self.log_config["handlers"]["file"]["filename"],
                "error_file": self.log_config["handlers"]["errors"]["filename"],
                "level_console": logging.getLevelName(self.log_config["handlers"]["console"]["level"]).lower(),
                "level_logfile": logging.getLevelName(self.log_config["handlers"]["file"]["level"]).lower(),
                "datefmt_console": self.log_config["formatters"]["console"]["datefmt"],
                "datefmt_logfile": self.log_config["formatters"]["file"]["datefmt"],
                "fmt_console": self.log_config["formatters"]["console"]["format"],
                "fmt_logfile": self.log_config["formatters"]["file"]["format"],
                "granular_levels": {},
            },
        }
        self._private_real_config = copy.deepcopy(self.__private_config)
        # select the correct config defaults based on the backend
        self._private_real_config["database"] = self.__private_database_map[db]

    def init_config(self, db):
        self._private_real_config = copy.deepcopy(self.__private_config)
        # select the correct config defaults based on the backend
        self._private_real_config["database"] = self.__private_database_map[db]
        return self._private_real_config

    def get(self):
        return self._private_real_config

    def set(self, config):
        self._private_real_config = config

    def get_db_key_map(sefl, db):
        return sefl.__private_database_keys_map[db]

    def get_db_map(sefl, db):
        return sefl.__private_database_map[db]


DEFAULT_LOG_DIR = os.getcwd()
DEFAULT_LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "console": {
            "class": "logging.Formatter",
            "format": (
                "[%(asctime)s] [%(levelname)s] (%(name)s) " "%(message)s (%(processName)-10s - pid: %(process)d)"
            ),
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
        "file": {
            "class": "logging.Formatter",
            "format": (
                "[%(asctime)s] [%(levelname)s] (%(name)s) " "%(message)s (%(processName)-10s - pid: %(process)d)"
            ),
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "console",
            "level": logging.INFO,
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": os.path.join(DEFAULT_LOG_DIR, "planetmint.log"),
            "mode": "w",
            "maxBytes": 209715200,
            "backupCount": 5,
            "formatter": "file",
            "level": logging.INFO,
        },
        "errors": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": os.path.join(DEFAULT_LOG_DIR, "planetmint-errors.log"),
            "mode": "w",
            "maxBytes": 209715200,
            "backupCount": 5,
            "formatter": "file",
            "level": logging.ERROR,
        },
    },
    "loggers": {},
    "root": {
        "level": logging.DEBUG,
        "handlers": ["console", "file", "errors"],
    },
}
