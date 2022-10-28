# Copyright © 2020 Interplanetary Database Association e.V.,
# Planetmint and IPDB software contributors.
# SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
# Code is Apache-2.0 and docs are CC-BY-4.0

# # Double Spend testing
# This test challenge the system with double spends.
from uuid import uuid4
from threading import Thread
import queue

import planetmint_driver.exceptions
from planetmint_driver.crypto import generate_keypair

from .helper.hosts import Hosts


def test_double_create():
    hosts = Hosts("/shared/hostnames")
    pm = hosts.get_connection()
    alice = generate_keypair()

    results = queue.Queue()

    tx = pm.transactions.fulfill(
        pm.transactions.prepare(
            operation="CREATE", signers=alice.public_key, assets=[{"data": {"uuid": str(uuid4())}}]
        ),
        private_keys=alice.private_key,
    )

    def send_and_queue(tx):
        try:
            pm.transactions.send_commit(tx)
            results.put("OK")
        except planetmint_driver.exceptions.TransportError:
            results.put("FAIL")

    t1 = Thread(target=send_and_queue, args=(tx,))
    t2 = Thread(target=send_and_queue, args=(tx,))

    t1.start()
    t2.start()

    results = [results.get(timeout=2), results.get(timeout=2)]

    assert results.count("OK") == 1
    assert results.count("FAIL") == 1
