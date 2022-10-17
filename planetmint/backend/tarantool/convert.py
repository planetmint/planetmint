# Copyright © 2020 Interplanetary Database Association e.V.,
# Planetmint and IPDB software contributors.
# SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
# Code is Apache-2.0 and docs are CC-BY-4.0

"""Convert implementation for Tarantool"""

from planetmint.backend.utils import module_dispatch_registrar
from planetmint.backend import convert
from planetmint.backend.tarantool.connection import TarantoolDBConnection

register_query = module_dispatch_registrar(convert)


@register_query(TarantoolDBConnection)
def prepare_asset(connection, transaction_type, transaction_id, filter_operation, asset):
    asset_id = transaction_id
    if transaction_type not in filter_operation:
        asset_id = asset["id"]
    return tuple([asset, transaction_id, asset_id])


@register_query(TarantoolDBConnection)
def prepare_metadata(connection, transaction_id, metadata):
    return {"id": transaction_id, "metadata": metadata}
