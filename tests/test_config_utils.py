# Copyright © 2020 Interplanetary Database Association e.V.,
# Planetmint and IPDB software contributors.
# SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
# Code is Apache-2.0 and docs are CC-BY-4.0

import pytest
import planetmint

from unittest.mock import mock_open, patch
from planetmint.config import Config


@pytest.fixture(scope="function", autouse=True)
def clean_config(monkeypatch, request):
    original_config = Config().init_config("tarantool_db")
    backend = request.config.getoption("--database-backend")
    original_config["database"] = Config().get_db_map(backend)
    monkeypatch.setattr("planetmint.config", original_config)


def test_bigchain_instance_is_initialized_when_conf_provided():
    from planetmint import config_utils

    assert "CONFIGURED" not in Config().get()

    config_utils.set_config({"database": {"backend": "a"}})

    assert Config().get()["CONFIGURED"] is True


def test_load_validation_plugin_loads_default_rules_without_name():
    from planetmint import config_utils
    from planetmint.validation import BaseValidationRules

    assert config_utils.load_validation_plugin() == BaseValidationRules


def test_load_validation_plugin_raises_with_unknown_name():
    from pkg_resources import ResolutionError
    from planetmint import config_utils

    with pytest.raises(ResolutionError):
        config_utils.load_validation_plugin("bogus")


def test_load_validation_plugin_raises_with_invalid_subclass(monkeypatch):
    # Monkeypatch entry_point.load to return something other than a
    # ValidationRules instance
    from planetmint import config_utils
    import time

    monkeypatch.setattr(
        config_utils, "iter_entry_points", lambda *args: [type("entry_point", (object,), {"load": lambda: object})]
    )

    with pytest.raises(TypeError):
        # Since the function is decorated with `lru_cache`, we need to
        # "miss" the cache using a name that has not been used previously
        config_utils.load_validation_plugin(str(time.time()))


def test_load_events_plugins(monkeypatch):
    from planetmint import config_utils

    monkeypatch.setattr(
        config_utils, "iter_entry_points", lambda *args: [type("entry_point", (object,), {"load": lambda: object})]
    )

    plugins = config_utils.load_events_plugins(["one", "two"])
    assert len(plugins) == 2


def test_map_leafs_iterator():
    from planetmint import config_utils

    mapping = {"a": {"b": {"c": 1}, "d": {"z": 44}}, "b": {"d": 2}, "c": 3}

    result = config_utils.map_leafs(lambda x, path: x * 2, mapping)
    assert result == {"a": {"b": {"c": 2}, "d": {"z": 88}}, "b": {"d": 4}, "c": 6}

    result = config_utils.map_leafs(lambda x, path: path, mapping)
    assert result == {
        "a": {"b": {"c": ["a", "b", "c"]}, "d": {"z": ["a", "d", "z"]}},
        "b": {"d": ["b", "d"]},
        "c": ["c"],
    }


def test_update_types():
    from planetmint import config_utils

    raw = {
        "a_string": "test",
        "an_int": "42",
        "a_float": "3.14",
        "a_list": "a:b:c",
    }

    reference = {
        "a_string": "test",
        "an_int": 42,
        "a_float": 3.14,
        "a_list": ["a", "b", "c"],
    }

    result = config_utils.update_types(raw, reference)
    assert result == reference


def test_env_config(monkeypatch):
    monkeypatch.setattr(
        "os.environ", {"PLANETMINT_DATABASE_HOST": "test-host", "PLANETMINT_DATABASE_PORT": "test-port"}
    )

    from planetmint import config_utils

    result = config_utils.env_config({"database": {"host": None, "port": None}})
    expected = {"database": {"host": "test-host", "port": "test-port"}}

    assert result == expected


@pytest.mark.skip
def test_autoconfigure_read_both_from_file_and_env(
    monkeypatch, request
):  # TODO Disabled until we create a better config format
    return
    # constants
    DATABASE_HOST = "test-host"
    DATABASE_NAME = "test-dbname"
    DATABASE_PORT = 4242
    DATABASE_BACKEND = request.config.getoption("--database-backend")
    SERVER_BIND = "1.2.3.4:56"
    WSSERVER_SCHEME = "ws"
    WSSERVER_HOST = "1.2.3.4"
    WSSERVER_PORT = 57
    WSSERVER_ADVERTISED_SCHEME = "wss"
    WSSERVER_ADVERTISED_HOST = "a.b.c.d"
    WSSERVER_ADVERTISED_PORT = 89
    LOG_FILE = "/somewhere/something.log"

    file_config = {
        "database": {"host": DATABASE_HOST},
        "log": {
            "level_console": "debug",
        },
    }

    monkeypatch.setattr("planetmint.config_utils.file_config", lambda *args, **kwargs: file_config)

    monkeypatch.setattr(
        "os.environ",
        {
            "PLANETMINT_DATABASE_NAME": DATABASE_NAME,
            "PLANETMINT_DATABASE_PORT": str(DATABASE_PORT),
            "PLANETMINT_DATABASE_BACKEND": DATABASE_BACKEND,
            "PLANETMINT_SERVER_BIND": SERVER_BIND,
            "PLANETMINT_WSSERVER_SCHEME": WSSERVER_SCHEME,
            "PLANETMINT_WSSERVER_HOST": WSSERVER_HOST,
            "PLANETMINT_WSSERVER_PORT": WSSERVER_PORT,
            "PLANETMINT_WSSERVER_ADVERTISED_SCHEME": WSSERVER_ADVERTISED_SCHEME,
            "PLANETMINT_WSSERVER_ADVERTISED_HOST": WSSERVER_ADVERTISED_HOST,
            "PLANETMINT_WSSERVER_ADVERTISED_PORT": WSSERVER_ADVERTISED_PORT,
            "PLANETMINT_LOG_FILE": LOG_FILE,
            "PLANETMINT_LOG_FILE": LOG_FILE,
            "PLANETMINT_DATABASE_CA_CERT": "ca_cert",
            "PLANETMINT_DATABASE_CRLFILE": "crlfile",
            "PLANETMINT_DATABASE_CERTFILE": "certfile",
            "PLANETMINT_DATABASE_KEYFILE": "keyfile",
            "PLANETMINT_DATABASE_KEYFILE_PASSPHRASE": "passphrase",
        },
    )

    from planetmint import config_utils
    from planetmint.log import DEFAULT_LOGGING_CONFIG as log_config

    config_utils.autoconfigure()

    database_mongodb = {
        "backend": "localmongodb",
        "host": DATABASE_HOST,
        "port": DATABASE_PORT,
        "name": DATABASE_NAME,
        "connection_timeout": 5000,
        "max_tries": 3,
        "replicaset": None,
        "ssl": False,
        "login": None,
        "password": None,
        "ca_cert": "ca_cert",
        "certfile": "certfile",
        "keyfile": "keyfile",
        "keyfile_passphrase": "passphrase",
        "crlfile": "crlfile",
    }

    assert planetmint.config == {
        "CONFIGURED": True,
        "server": {
            "bind": SERVER_BIND,
            "loglevel": "info",
            "workers": None,
        },
        "wsserver": {
            "scheme": WSSERVER_SCHEME,
            "host": WSSERVER_HOST,
            "port": WSSERVER_PORT,
            "advertised_scheme": WSSERVER_ADVERTISED_SCHEME,
            "advertised_host": WSSERVER_ADVERTISED_HOST,
            "advertised_port": WSSERVER_ADVERTISED_PORT,
        },
        "database": database_mongodb,
        "tendermint": {"host": "localhost", "port": 26657, "version": "v0.34.15"},
        "log": {
            "file": LOG_FILE,
            "level_console": "debug",
            "error_file": log_config["handlers"]["errors"]["filename"],
            "level_console": "debug",
            "level_logfile": "info",
            "datefmt_console": log_config["formatters"]["console"]["datefmt"],
            "datefmt_logfile": log_config["formatters"]["file"]["datefmt"],
            "fmt_console": log_config["formatters"]["console"]["format"],
            "fmt_logfile": log_config["formatters"]["file"]["format"],
            "granular_levels": {},
        },
    }


def test_autoconfigure_env_precedence(monkeypatch):
    file_config = {"database": {"host": "test-host", "name": "planetmint", "port": 28015}}
    monkeypatch.setattr("planetmint.config_utils.file_config", lambda *args, **kwargs: file_config)
    monkeypatch.setattr(
        "os.environ",
        {
            "PLANETMINT_DATABASE_NAME": "test-dbname",
            "PLANETMINT_DATABASE_PORT": 4242,
            "PLANETMINT_SERVER_BIND": "localhost:9985",
        },
    )
    from planetmint import config_utils
    from planetmint.config import Config

    config_utils.autoconfigure()

    assert Config().get()["CONFIGURED"]
    assert Config().get()["database"]["host"] == "test-host"
    assert Config().get()["database"]["name"] == "test-dbname"
    assert Config().get()["database"]["port"] == 4242
    assert Config().get()["server"]["bind"] == "localhost:9985"


def test_autoconfigure_explicit_file(monkeypatch):
    from planetmint import config_utils

    def file_config(*args, **kwargs):
        raise FileNotFoundError()

    monkeypatch.setattr("planetmint.config_utils.file_config", file_config)

    with pytest.raises(FileNotFoundError):
        config_utils.autoconfigure(filename="autoexec.bat")


def test_update_config(monkeypatch):
    from planetmint import config_utils

    file_config = {"database": {"host": "test-host", "name": "planetmint", "port": 28015}}
    monkeypatch.setattr("planetmint.config_utils.file_config", lambda *args, **kwargs: file_config)
    config_utils.autoconfigure(config=file_config)

    # update configuration, retaining previous changes
    config_utils.update_config({"database": {"port": 28016, "name": "planetmint_other"}})

    assert Config().get()["database"]["host"] == "test-host"
    assert Config().get()["database"]["name"] == "planetmint_other"
    assert Config().get()["database"]["port"] == 28016


def test_file_config():
    from planetmint.config_utils import file_config, CONFIG_DEFAULT_PATH

    with patch("builtins.open", mock_open(read_data="{}")) as m:
        config = file_config()
    m.assert_called_once_with(CONFIG_DEFAULT_PATH)
    assert config == {}


def test_invalid_file_config():
    from planetmint.config_utils import file_config
    from transactions.common import exceptions

    with patch("builtins.open", mock_open(read_data="{_INVALID_JSON_}")):
        with pytest.raises(exceptions.ConfigurationError):
            file_config()


def test_write_config():
    from planetmint.config_utils import write_config, CONFIG_DEFAULT_PATH

    m = mock_open()
    with patch("builtins.open", m):
        write_config({})
    m.assert_called_once_with(CONFIG_DEFAULT_PATH, "w")
    handle = m()
    handle.write.assert_called_once_with("{}")


@pytest.mark.parametrize(
    "env_name,env_value,config_key",
    (
        ("PLANETMINT_DATABASE_BACKEND", "test-backend", "backend"),
        ("PLANETMINT_DATABASE_HOST", "test-host", "host"),
        ("PLANETMINT_DATABASE_PORT", 4242, "port"),
        ("PLANETMINT_DATABASE_NAME", "test-db", "name"),
    ),
)
def test_database_envs(env_name, env_value, config_key, monkeypatch):

    monkeypatch.setattr("os.environ", {env_name: env_value})
    planetmint.config_utils.autoconfigure()

    expected_config = Config().get()
    expected_config["database"][config_key] = env_value

    assert planetmint.config == expected_config
