# Copyright © 2020 Interplanetary Database Association e.V.,
# Planetmint and IPDB software contributors.
# SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
# Code is Apache-2.0 and docs are CC-BY-4.0

"""Generic backend database interfaces expected by Planetmint.

The interfaces in this module allow Planetmint to be agnostic about its
database backend. One can configure Planetmint to use different databases as
its data store by setting the ``database.backend`` property in the
configuration or the ``PLANETMINT_DATABASE_BACKEND`` environment variable.
"""

# Include the backend interfaces
from planetmint.backend import schema, query  # noqa
from planetmint.backend.connection import Connection
