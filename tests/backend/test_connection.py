# Copyright © 2020 Interplanetary Database Association e.V.,
# Planetmint and IPDB software contributors.
# SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
# Code is Apache-2.0 and docs are CC-BY-4.0

import pytest


def test_get_connection_raises_a_configuration_error(monkeypatch):
    from planetmint.transactions.common.exceptions import ConfigurationError
    from planetmint.backend.connection import Connection
    with pytest.raises(ConfigurationError):
        Connection('msaccess', 'localhost', '1337', 'mydb')

    with pytest.raises(ConfigurationError):
        # We need to force a misconfiguration here
        monkeypatch.setattr('planetmint.backend.connection.BACKENDS',
                            {'catsandra':
                             'planetmint.backend.meowmeow.Catsandra'})

        Connection('catsandra', 'localhost', '1337', 'mydb')
