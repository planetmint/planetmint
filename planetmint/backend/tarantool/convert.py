# Copyright © 2020 Interplanetary Database Association e.V.,
# Planetmint and IPDB software contributors.
# SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
# Code is Apache-2.0 and docs are CC-BY-4.0

"""Convert implementation for Tarantool"""

from planetmint.backend.utils import module_dispatch_registrar
from planetmint.backend import convert
from planetmint.backend.tarantool.connection import TarantoolDBConnection
from transactions import Transaction

register_query = module_dispatch_registrar(convert)


@register_query(TarantoolDBConnection)
def prepare_asset(connection, transaction: Transaction, filter_operation, assets):
    asset_id = transaction.id
    if transaction.operation not in filter_operation:
        asset_id = Transaction.read_out_asset_id(transaction)
    return tuple([assets, transaction.id, asset_id])


@register_query(TarantoolDBConnection)
def prepare_metadata(connection, transaction: Transaction, metadata):
    return {"id": transaction.id, "metadata": metadata}
