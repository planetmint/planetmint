# Copyright © 2020 Interplanetary Database Association e.V.,
# Planetmint and IPDB software contributors.
# SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
# Code is Apache-2.0 and docs are CC-BY-4.0

from typing import List

from planetmint_driver import Planetmint


class Hosts:
    hostnames = []
    connections = []

    def __init__(self, filepath):
        self.set_hostnames(filepath=filepath)
        self.set_connections()

    def set_hostnames(self, filepath) -> None:
        with open(filepath) as f:
            self.hostnames = f.readlines()

    def set_connections(self) -> None:
        self.connections = list(map(lambda h: Planetmint(h), self.hostnames))

    def get_connection(self, index=0) -> Planetmint:
        return self.connections[index]

    def get_transactions(self, tx_id) -> List:
        return list(map(lambda connection: connection.transactions.retrieve(tx_id), self.connections))

    def assert_transaction(self, tx_id) -> None:
        txs = self.get_transactions(tx_id)
        for tx in txs:
            assert txs[0] == tx, "Cannot find transaction {}".format(tx_id)
