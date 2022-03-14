# Copyright © 2020 Interplanetary Database Association e.V.,
# Planetmint and IPDB software contributors.
# SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
# Code is Apache-2.0 and docs are CC-BY-4.0

from typing import List

from planetmint_driver import Planetmint

class Hosts:
    hosts = []
    connections = []

    def __init__(self, filepath):
        self.set_hosts(filepath=filepath)
        self.set_connections()

    def set_hosts(self, filepath) -> None:
        with open(filepath) as f:
            self.hosts = f.readlines()

    def set_connections(self) -> None:
        self.connections = list(map(lambda h: Planetmint(h), self.hosts))

    # Not sure if necessary for certain test scenarios
    def get_alpha(self) -> Planetmint:
        return self.connections[0]

    # Not sure if necessary for certain test scenarios
    def get_betas(self) -> List[Planetmint]:
        return self.connections[1:]

    def get_transactions(self, tx_id) -> List:
        return list(map(lambda connection: connection.transactions.retrieve(tx_id), self.connections))

    # TODO: pass optional arguments to assert certain prperties of transaction
    def assert_transaction(self, tx_id) -> None:
        txs = self.get_transactions(tx_id)
        for tx in txs:
            assert txs[0] == tx, \
                'Cannot find transaction {}'.format(tx_id)