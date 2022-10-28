# Copyright © 2020 Interplanetary Database Association e.V.,
# Planetmint and IPDB software contributors.
# SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
# Code is Apache-2.0 and docs are CC-BY-4.0

# import Planetmint and create object
from planetmint_driver.crypto import generate_keypair

# import helper to manage multiple nodes
from .helper.hosts import Hosts

import time


def test_basic():
    # Setup up connection to Planetmint integration test nodes
    hosts = Hosts("/shared/hostnames")
    pm_alpha = hosts.get_connection()

    # genarate a keypair
    alice = generate_keypair()

    # create a digital asset for Alice
    game_boy_token = [
        {
            "data": {
                "hash": "0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF",
                "storageID": "0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF",
            },
        }
    ]

    # prepare the transaction with the digital asset and issue 10 tokens to bob
    prepared_creation_tx = pm_alpha.transactions.prepare(
        operation="CREATE",
        metadata={
            "hash": "0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF",
            "storageID": "0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF",
        },
        signers=alice.public_key,
        recipients=[([alice.public_key], 10)],
        assets=game_boy_token,
    )

    # fulfill and send the transaction
    fulfilled_creation_tx = pm_alpha.transactions.fulfill(prepared_creation_tx, private_keys=alice.private_key)
    pm_alpha.transactions.send_commit(fulfilled_creation_tx)
    time.sleep(1)

    creation_tx_id = fulfilled_creation_tx["id"]

    # Assert that transaction is stored on all planetmint nodes
    hosts.assert_transaction(creation_tx_id)

    # Transfer
    # create the output and inout for the transaction
    transfer_assets = [{"id": creation_tx_id}]
    output_index = 0
    output = fulfilled_creation_tx["outputs"][output_index]
    transfer_input = {
        "fulfillment": output["condition"]["details"],
        "fulfills": {"output_index": output_index, "transaction_id": transfer_assets[0]["id"]},
        "owners_before": output["public_keys"],
    }

    # prepare the transaction and use 3 tokens
    prepared_transfer_tx = pm_alpha.transactions.prepare(
        operation="TRANSFER",
        asset=transfer_assets,
        inputs=transfer_input,
        metadata={
            "hash": "0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF",
            "storageID": "0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF",
        },
        recipients=[([alice.public_key], 10)],
    )

    # fulfill and send the transaction
    fulfilled_transfer_tx = pm_alpha.transactions.fulfill(prepared_transfer_tx, private_keys=alice.private_key)
    sent_transfer_tx = pm_alpha.transactions.send_commit(fulfilled_transfer_tx)

    time.sleep(1)

    transfer_tx_id = sent_transfer_tx["id"]

    # Assert that transaction is stored on both planetmint nodes
    hosts.assert_transaction(transfer_tx_id)
