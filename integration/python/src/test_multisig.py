# Copyright © 2020 Interplanetary Database Association e.V.,
# Planetmint and IPDB software contributors.
# SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
# Code is Apache-2.0 and docs are CC-BY-4.0

# # Multisignature integration testing
# This test checks if we can successfully create and transfer a transaction
# with multiple owners.
# The script tests various things like:
#
# - create a transaction with multiple owners
# - check if the transaction is stored and has the right amount of public keys
# - transfer the transaction to a third person
#
# We run a series of checks for each step, that is retrieving
# the transaction from the remote system, and also checking the public keys
# of a given transaction.
#
# This integration test is a rip-off of our mutliple signature acceptance tests.

# ## Imports
# We need some utils from the `os` package, we will interact with
# env variables.
import os

# For this test case we need import and use the Python driver
from planetmint_driver import Planetmint
from planetmint_driver.crypto import generate_keypair

def test_multiple_owners():
    # ## Set up a connection to the Planetmint integration test nodes
    pm_itest1 = Planetmint(os.environ.get('PLANETMINT_ENDPOINT_1'))
    pm_itest2 = Planetmint(os.environ.get('PLANETMINT_ENDPOINT_2'))

    # Generate Keypairs for Alice and Bob!
    alice, bob = generate_keypair(), generate_keypair()

    # ## Alice and Bob create a transaction
    # Alice and Bob just moved into a shared flat, no one can afford these
    # high rents anymore. Bob suggests to get a dish washer for the
    # kitchen. Alice agrees and here they go, creating the asset for their
    # dish washer.
    dw_asset = {
        'data': {
            'dish washer': {
                'serial_number': 1337
            }
        }
    }

    # They prepare a `CREATE` transaction. To have multiple owners, both
    # Bob and Alice need to be the recipients.
    prepared_dw_tx = pm_itest1.transactions.prepare(
        operation='CREATE',
        signers=alice.public_key,
        recipients=(alice.public_key, bob.public_key),
        asset=dw_asset)

    # Now they both sign the transaction by providing their private keys.
    # And send it afterwards.
    fulfilled_dw_tx = pm_itest1.transactions.fulfill(
        prepared_dw_tx,
        private_keys=[alice.private_key, bob.private_key])

    pm_itest1.transactions.send_commit(fulfilled_dw_tx)

    # We store the `id` of the transaction to use it later on.
    dw_id = fulfilled_dw_tx['id']

    # Let's retrieve the transaction from both nodes
    pm_itest1_tx = pm_itest1.transactions.retrieve(dw_id)
    pm_itest2_tx = pm_itest2.transactions.retrieve(dw_id)

    # Both retrieved transactions should be the same
    assert pm_itest1_tx == pm_itest2_tx

    # Let's check if the transaction was successful.
    assert pm_itest1.transactions.retrieve(dw_id), \
        'Cannot find transaction {}'.format(dw_id)

    # The transaction should have two public keys in the outputs.
    assert len(
        pm_itest1.transactions.retrieve(dw_id)['outputs'][0]['public_keys']) == 2

    # ## Alice and Bob transfer a transaction to Carol.
    # Alice and Bob save a lot of money living together. They often go out
    # for dinner and don't cook at home. But now they don't have any dishes to
    # wash, so they decide to sell the dish washer to their friend Carol.

    # Hey Carol, nice to meet you!
    carol = generate_keypair()

    # Alice and Bob prepare the transaction to transfer the dish washer to
    # Carol.
    transfer_asset = {'id': dw_id}

    output_index = 0
    output = fulfilled_dw_tx['outputs'][output_index]
    transfer_input = {'fulfillment': output['condition']['details'],
                      'fulfills': {'output_index': output_index,
                                   'transaction_id': fulfilled_dw_tx[
                                       'id']},
                      'owners_before': output['public_keys']}

    # Now they create the transaction...
    prepared_transfer_tx = pm_itest1.transactions.prepare(
        operation='TRANSFER',
        asset=transfer_asset,
        inputs=transfer_input,
        recipients=carol.public_key)

    # ... and sign it with their private keys, then send it.
    fulfilled_transfer_tx = pm_itest1.transactions.fulfill(
        prepared_transfer_tx,
        private_keys=[alice.private_key, bob.private_key])

    sent_transfer_tx = pm_itest1.transactions.send_commit(fulfilled_transfer_tx)

    # Retrieve the fulfilled transaction from both nodes
    pm_itest1_tx = pm_itest1.transactions.retrieve(fulfilled_transfer_tx['id'])
    pm_itest2_tx = pm_itest2.transactions.retrieve(fulfilled_transfer_tx['id'])

    # Now compare if both nodes returned the same transaction
    assert pm_itest1_tx == pm_itest2_tx

    # They check if the transaction was successful.
    assert pm_itest1.transactions.retrieve(
        fulfilled_transfer_tx['id']) == sent_transfer_tx

    # The owners before should include both Alice and Bob.
    assert len(
        pm_itest1.transactions.retrieve(fulfilled_transfer_tx['id'])['inputs'][0][
            'owners_before']) == 2

    # While the new owner is Carol.
    assert pm_itest1.transactions.retrieve(fulfilled_transfer_tx['id'])[
           'outputs'][0]['public_keys'][0] == carol.public_key
    