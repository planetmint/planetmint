# Copyright © 2020 Interplanetary Database Association e.V.,
# Planetmint and IPDB software contributors.
# SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
# Code is Apache-2.0 and docs are CC-BY-4.0


def test_settings():
    from planetmint.config import Config
    from planetmint.web import server

    s = server.create_server(Config().get()['server'])

    # for whatever reason the value is wrapped in a list
    # needs further investigation
    assert s.cfg.bind[0] == Config().get()['server']['bind']
