# Copyright © 2020 Interplanetary Database Association e.V.,
# Planetmint and IPDB software contributors.
# SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
# Code is Apache-2.0 and docs are CC-BY-4.0

import pytest


@pytest.fixture
def app(request):
    from planetmint.web import server
    from planetmint.application import Validator

    if request.config.getoption("--database-backend") == "localmongodb":
        app = server.create_app(debug=True, planetmint_factory=Validator)
    else:
        app = server.create_app(debug=True)

    return app
