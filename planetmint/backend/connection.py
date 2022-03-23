# Copyright © 2020 Interplanetary Database Association e.V.,
# Planetmint and IPDB software contributors.
# SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
# Code is Apache-2.0 and docs are CC-BY-4.0

import logging
from importlib import import_module

from planetmint.backend.utils import get_planetmint_config_value

BACKENDS = {  # This is path to MongoDBClass
    'tarantool_db': 'planetmint.backend.tarantool.connection.TarantoolDB',
    'localmongodb': 'planetmint.backend.localmongodb.connection.LocalMongoDBConnection'
}

logger = logging.getLogger(__name__)


# backend = get_planetmint_config_value("backend")
# if not backend:
#     backend = 'tarantool_db'
#
# modulepath, _, class_name = BACKENDS[backend].rpartition('.')
# current_backend = getattr(import_module(modulepath), class_name)


def Connection(host: str = None, port: int = None, login: str = None, password: str = None, backend: str = None,
               **kwargs):
    # TODO To add parser for **kwargs, when mongodb is used
    backend = backend or get_planetmint_config_value("backend") if not kwargs.get("backend") else kwargs["backend"]
    host = host or get_planetmint_config_value("host") if kwargs.get("host") is None else kwargs["host"]
    port = port or get_planetmint_config_value("port") if not kwargs.get("port") is None else kwargs["port"]
    login = login or get_planetmint_config_value("login") if not kwargs.get("login") is None else kwargs["login"]
    password = password or get_planetmint_config_value("password")

    if backend == "tarantool_db":
        modulepath, _, class_name = BACKENDS[backend].rpartition('.')
        Class = getattr(import_module(modulepath), class_name)
        return Class(host=host, port=port, user=login, password=password)
    elif backend == "localmongodb":
        modulepath, _, class_name = BACKENDS[backend].rpartition('.')
        Class = getattr(import_module(modulepath), class_name)

        dbname = _kwargs_parser(key="name", kwargs=kwargs) or get_planetmint_config_value('name')
        replicaset = _kwargs_parser(key="replicaset", kwargs=kwargs) or get_planetmint_config_value('replicaset')
        ssl = _kwargs_parser(key="ssl", kwargs=kwargs) or get_planetmint_config_value('ssl', False)
        login = login or get_planetmint_config_value('login') if _kwargs_parser(key="login", kwargs=kwargs) is None else _kwargs_parser(key="login", kwargs=kwargs)
        password = password or get_planetmint_config_value('password') if _kwargs_parser(key="password", kwargs=kwargs) is None else _kwargs_parser(key="password", kwargs=kwargs)
        ca_cert = _kwargs_parser(key="ca_cert", kwargs=kwargs) or get_planetmint_config_value('ca_cert')
        certfile = _kwargs_parser(key="certfile", kwargs=kwargs) or get_planetmint_config_value('certfile')
        keyfile = _kwargs_parser(key="keyfile", kwargs=kwargs) or get_planetmint_config_value('keyfile')
        keyfile_passphrase = _kwargs_parser(key="keyfile_passphrase", kwargs=kwargs) or get_planetmint_config_value('keyfile_passphrase', None)
        crlfile = _kwargs_parser(key="crlfile", kwargs=kwargs) or get_planetmint_config_value('crlfile')
        max_tries = _kwargs_parser(key="max_tries", kwargs=kwargs)
        connection_timeout = _kwargs_parser(key="connection_timeout", kwargs=kwargs)

        return Class(host=host, port=port, dbname=dbname,
                     max_tries=max_tries, connection_timeout=connection_timeout,
                     replicaset=replicaset, ssl=ssl, login=login, password=password,
                     ca_cert=ca_cert, certfile=certfile, keyfile=keyfile,
                     keyfile_passphrase=keyfile_passphrase, crlfile=crlfile)


def _kwargs_parser(key, kwargs):
    if kwargs.get(key):
        return kwargs[key]
    return None
