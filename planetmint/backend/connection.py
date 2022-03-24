# Copyright © 2020 Interplanetary Database Association e.V.,
# Planetmint and IPDB software contributors.
# SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
# Code is Apache-2.0 and docs are CC-BY-4.0

import logging
from importlib import import_module
from planetmint.config import Config

BACKENDS = {  # This is path to MongoDBClass
    'tarantool_db': 'planetmint.backend.tarantool.connection.TarantoolDB',
    'localmongodb': 'planetmint.backend.localmongodb.connection.LocalMongoDBConnection'
}

logger = logging.getLogger(__name__)


def Connection(host: str = None, port: int = None, login: str = None, password: str = None, backend: str = None,
               **kwargs):
    backend = backend
    if not backend and kwargs and kwargs["backend"]:
        backend = kwargs["backend"]

    if backend and backend != Config().get()["database"]["backend"]:
        Config().init_config(backend)
    else:
        backend = Config().get()["database"]["backend"]

    host = host or Config().get()["database"]["host"] if not kwargs.get("host") else kwargs["host"]
    port = port or Config().get()['database']['port'] if not kwargs.get("port") else kwargs["port"]
    login = login or Config().get()["database"]["login"] if not kwargs.get("login") else kwargs["login"]
    password = password or Config().get()["database"]["password"]
    if backend == "tarantool_db":
        modulepath, _, class_name = BACKENDS[backend].rpartition('.')
        Class = getattr(import_module(modulepath), class_name)
        print("LOGIN " + str(login))
        print("PASSWORD " + str(password))
        return Class(host=host, port=port, user=login, password=password)
    elif backend == "localmongodb":
        modulepath, _, class_name = BACKENDS[backend].rpartition('.')
        Class = getattr(import_module(modulepath), class_name)
        print(Config().get())
        dbname = _kwargs_parser(key="name", kwargs=kwargs) or Config().get()['database']['name']
        replicaset = _kwargs_parser(key="replicaset", kwargs=kwargs) or Config().get()['database']['replicaset']
        ssl = _kwargs_parser(key="ssl", kwargs=kwargs) or Config().get()['database']['ssl']
        login = login or Config().get()['database']['login'] if _kwargs_parser(key="login",
                                                                               kwargs=kwargs) is None else _kwargs_parser(
            key="login", kwargs=kwargs)
        password = password or Config().get()['database']['password'] if _kwargs_parser(key="password",
                                                                                        kwargs=kwargs) is None else _kwargs_parser(
            key="password", kwargs=kwargs)
        ca_cert = _kwargs_parser(key="ca_cert", kwargs=kwargs) or Config().get()['database']['ca_cert']
        certfile = _kwargs_parser(key="certfile", kwargs=kwargs) or Config().get()['database']['certfile']
        keyfile = _kwargs_parser(key="keyfile", kwargs=kwargs) or Config().get()['database']['keyfile']
        keyfile_passphrase = _kwargs_parser(key="keyfile_passphrase", kwargs=kwargs) or Config().get()['database'][
            'keyfile_passphrase']
        crlfile = _kwargs_parser(key="crlfile", kwargs=kwargs) or Config().get()['database']['crlfile']
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
