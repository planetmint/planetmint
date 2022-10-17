# Copyright © 2020 Interplanetary Database Association e.V.,
# Planetmint and IPDB software contributors.
# SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
# Code is Apache-2.0 and docs are CC-BY-4.0


class FastTransaction:
    """A minimal wrapper around a transaction dictionary. This is useful for
    when validation is not required but a routine expects something that looks
    like a transaction, for example during block creation.

    Note: immutability could also be provided
    """

    def __init__(self, tx_dict):
        self.data = tx_dict

    @property
    def id(self):
        return self.data["id"]

    def to_dict(self):
        return self.data
