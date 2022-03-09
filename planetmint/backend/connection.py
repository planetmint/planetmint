# Copyright © 2020 Interplanetary Database Association e.V.,
# Planetmint and IPDB software contributors.
# SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
# Code is Apache-2.0 and docs are CC-BY-4.0

import sys
import logging
from importlib import import_module
from itertools import repeat

from planetmint.backend.exceptions import ConnectionError
from planetmint.backend.utils import get_planetmint_config_value, get_planetmint_config_value_or_key_error
from planetmint.common.exceptions import ConfigurationError

BACKENDS = {  # This is path to MongoDBClass
    'tarantool_db': 'planetmint.backend.tarantool.connection.TarantoolDB',
    'localmongodb': 'planetmint.backend.localmongodb.connection.LocalMongoDBConnection'
}

logger = logging.getLogger(__name__)


modulename = sys.modules[__name__]
backend = get_planetmint_config_value("backend")
current_backend = getattr(modulename, BACKENDS[backend])


class Connection(current_backend):
    pass


