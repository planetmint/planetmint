# Copyright © 2020 Interplanetary Database Association e.V.,
# Planetmint and IPDB software contributors.
# SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
# Code is Apache-2.0 and docs are CC-BY-4.0

# import Planetmint and create object
from planetmint_driver import Planetmint
from planetmint_driver.crypto import generate_keypair
import time
import os


def test_basic():
    # Setup up connection to Planetmint integration test nodes
    pm_itest1_url = os.environ.get('PLANETMINT_ENDPOINT_1')
    pm_itest2_url = os.environ.get('PLANETMINT_ENDPOINT_1')
    pm_itest1 = Planetmint(pm_itest1_url)
    pm_itest2 = Planetmint(pm_itest2_url)

    # genarate a keypair
    alice, bob = generate_keypair(), generate_keypair()

    # create a digital asset for Alice
    game_boy_token = {
        'data': {
            'hash': '0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF',
            'storageID': '0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF',
        },
    }

    # prepare the transaction with the digital asset and issue 10 tokens to bob
    prepared_creation_tx = pm_itest1.transactions.prepare(
        operation='CREATE',
        metadata={
            'hash': '0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF',
            'storageID': '0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF',},
        signers=alice.public_key,
        recipients=[([alice.public_key], 10)],
        asset=game_boy_token)

    # fulfill and send the transaction
    fulfilled_creation_tx = pm_itest1.transactions.fulfill(
        prepared_creation_tx,
        private_keys=alice.private_key)
    pm_itest1.transactions.send_commit(fulfilled_creation_tx)
    time.sleep(4)

    creation_tx_id = fulfilled_creation_tx['id']

    # retrieve transactions from both planetmint nodes
    creation_tx_itest1 = pm_itest1.transactions.retrieve(creation_tx_id)
    creation_tx_itest2 = pm_itest2.transactions.retrieve(creation_tx_id)

    # Assert that transaction is stored on both planetmint nodes
    assert creation_tx_itest1 == creation_tx_itest2

    # Transfer
    # create the output and inout for the transaction
    transfer_asset = {'id': creation_tx_id}
    output_index = 0
    output = fulfilled_creation_tx['outputs'][output_index]
    transfer_input = {'fulfillment': output['condition']['details'],
                      'fulfills': {'output_index': output_index,
                                   'transaction_id': transfer_asset['id']},
                      'owners_before': output['public_keys']}

    # prepare the transaction and use 3 tokens
    prepared_transfer_tx = pm_itest1.transactions.prepare(
        operation='TRANSFER',
        asset=transfer_asset,
        inputs=transfer_input,
        metadata={'hash': '0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF',
                'storageID': '0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF', },
        recipients=[([alice.public_key], 10)])

    # fulfill and send the transaction
    fulfilled_transfer_tx = pm_itest1.transactions.fulfill(
        prepared_transfer_tx,
        private_keys=alice.private_key)
    sent_transfer_tx = pm_itest1.transactions.send_commit(fulfilled_transfer_tx)

    transfer_tx_id = fulfilled_transfer_tx['id']

    # retrieve transactions from both planetmint nodes
    transfer_tx_itest1 = pm_itest1.transactions.retrieve(transfer_tx_id)
    transfer_tx_itest2 = pm_itest2.transactions.retrieve(transfer_tx_id)

    # Assert that transaction is stored on both planetmint nodes
    assert transfer_tx_itest1 == transfer_tx_itest2




    
    




