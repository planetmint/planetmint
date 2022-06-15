# Copyright © 2020 Interplanetary Database Association e.V.,
# Planetmint and IPDB software contributors.
# SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
# Code is Apache-2.0 and docs are CC-BY-4.0

import copy
import logging

from planetmint.log import DEFAULT_LOGGING_CONFIG as log_config
from planetmint.lib import Planetmint  # noqa
from planetmint.transactions.types.elections.chain_migration_election import ChainMigrationElection
from planetmint.version import __version__  # noqa
from planetmint.core import App  # noqa

# from functools import reduce
# PORT_NUMBER = reduce(lambda x, y: x * y, map(ord, 'Planetmint')) % 2**16
# basically, the port number is 9984

# The following variable is used by `planetmint configure` to
# prompt the user for database values. We cannot rely on
# _base_database_localmongodb.keys() because dicts are unordered.
# I tried to configure

_database_keys_map = {
    'localmongodb': ('host', 'port', 'name'),
}

_base_database_localmongodb = {
    'host': 'localhost',
    'port': 27017,
    'name': 'bigchain',
    'replicaset': None,
    'login': None,
    'password': None,
}

_database_localmongodb = {
    'backend': 'localmongodb',
    'connection_timeout': 5000,
    'max_tries': 3,
    'ssl': False,
    'ca_cert': None,
    'certfile': None,
    'keyfile': None,
    'keyfile_passphrase': None,
    'crlfile': None,
}
_database_localmongodb.update(_base_database_localmongodb)

_database_map = {
    'localmongodb': _database_localmongodb,
}

config = {
    'server': {
        # Note: this section supports all the Gunicorn settings:
        #       - http://docs.gunicorn.org/en/stable/settings.html
        'bind': 'localhost:9984',
        'loglevel': logging.getLevelName(
            log_config['handlers']['console']['level']).lower(),
        'workers': None,  # if None, the value will be cpu_count * 2 + 1
    },
    'wsserver': {
        'scheme': 'ws',
        'host': 'localhost',
        'port': 9985,
        'advertised_scheme': 'ws',
        'advertised_host': 'localhost',
        'advertised_port': 9985,
    },
    'tendermint': {
        'host': 'localhost',
        'port': 26657,
        'version': 'v0.34.15',  # look for __tm_supported_versions__
    },
    # FIXME: hardcoding to localmongodb for now
    'database': _database_map['localmongodb'],
    'log': {
        'file': log_config['handlers']['file']['filename'],
        'error_file': log_config['handlers']['errors']['filename'],
        'level_console': logging.getLevelName(
            log_config['handlers']['console']['level']).lower(),
        'level_logfile': logging.getLevelName(
            log_config['handlers']['file']['level']).lower(),
        'datefmt_console': log_config['formatters']['console']['datefmt'],
        'datefmt_logfile': log_config['formatters']['file']['datefmt'],
        'fmt_console': log_config['formatters']['console']['format'],
        'fmt_logfile': log_config['formatters']['file']['format'],
        'granular_levels': {},
    },
}

# We need to maintain a backup copy of the original config dict in case
# the user wants to reconfigure the node. Check ``planetmint.config_utils``
# for more info.
_config = copy.deepcopy(config)
from planetmint.transactions.common.transaction import Transaction  # noqa
from planetmint import models                          # noqa
from planetmint.upsert_validator import ValidatorElection  # noqa
from planetmint.transactions.types.elections.vote import Vote  # noqa

Transaction.register_type(Transaction.CREATE, models.Transaction)
Transaction.register_type(Transaction.TRANSFER, models.Transaction)
Transaction.register_type(ValidatorElection.OPERATION, ValidatorElection)
Transaction.register_type(ChainMigrationElection.OPERATION, ChainMigrationElection)
Transaction.register_type(Vote.OPERATION, Vote)
