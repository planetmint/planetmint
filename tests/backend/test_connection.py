# Copyright © 2020 Interplanetary Database Association e.V.,
# Planetmint and IPDB software contributors.
# SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
# Code is Apache-2.0 and docs are CC-BY-4.0

import pytest


def test_get_connection_raises_a_configuration_error(monkeypatch):
    from planetmint.transactions.common.exceptions import ConfigurationError, ConnectionError
    from planetmint.backend.connection import Connection
    from planetmint.backend.localmongodb.connection import LocalMongoDBConnection
    from planetmint.backend.tarantool.connection import TarantoolDBConnection

    with pytest.raises(ConnectionError):
        LocalMongoDBConnection("localhost", "1337", "mydb", "password")
    with pytest.raises(ConnectionError):
        TarantoolDBConnection("localhost", "1337", "mydb", "password")
