# Copyright © 2020 Interplanetary Database Association e.V.,
# Planetmint and IPDB software contributors.
# SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
# Code is Apache-2.0 and docs are CC-BY-4.0

"""Convert interfaces for backends."""

from functools import singledispatch


@singledispatch
def prepare_asset(connection, transaction_type, transaction_id, filter_operation, asset):
    """
    This function is used for preparing assets,
    before storing them to database.
    """
    raise NotImplementedError


@singledispatch
def prepare_metadata(connection, transaction_id, metadata):
    """
    This function is used for preparing metadata,
    before storing them to database.
    """
    raise NotImplementedError
