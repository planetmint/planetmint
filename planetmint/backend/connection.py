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
backend = get_planetmint_config_value("backend")
if not backend:
    backend = 'tarantool_db'    
    
modulepath, _, class_name = BACKENDS[backend].rpartition('.')
current_backend = getattr(import_module(modulepath), class_name)


class Connection(current_backend):
    pass
