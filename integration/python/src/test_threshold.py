# Copyright © 2020 Interplanetary Database Association e.V.,
# Planetmint and IPDB software contributors.
# SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
# Code is Apache-2.0 and docs are CC-BY-4.0

# ## Imports
import time
import json

# For this test case we need the planetmint_driver.crypto package
import base58
import sha3
import cryptoconditions as cc
from cryptoconditions import Ed25519Sha256, ThresholdSha256
from planetmint_driver import Planetmint
from planetmint_driver.crypto import generate_keypair
from planetmint_driver.common.transaction import Transaction, _fulfillment_to_details

# Import helper to deal with multiple nodes
from .helper.hosts import Hosts

# TODO: For testing purposes remove before merge
def make_ed25519_condition(public_key, *, amount=1):
    ed25519 = Ed25519Sha256(public_key=base58.b58decode(public_key))
    return {
        'amount': str(amount),
        'condition': {
            'details': _fulfillment_to_details(ed25519),
            'uri': ed25519.condition_uri,
        },
        'public_keys': (public_key,),
    }

# TODO: For testing purposes remove before merge
def make_threshold_condition(threshold, sub_conditions):
    threshold_condition = ThresholdSha256(threshold)
    for condition in sub_conditions:
        threshold_condition.add_subcondition(condition)
    return threshold_condition

def test_threshold():
    # Setup connection to test nodes
    hosts = Hosts('/shared/hostnames')
    pm = hosts.get_alpha()

    # Generate Keypars for Alice, Bob an Carol!
    alice, bob, carol = generate_keypair(), generate_keypair(), generate_keypair()

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

    # References:
    # http://docs.bigchaindb.com/projects/py-driver/en/latest/handcraft.html#multiple-owners-with-m-of-n-signatures
    # https://buildmedia.readthedocs.org/media/pdf/bigchaindb/v0.4.0/bigchaindb.pdf
    # https://github.com/bigchaindb/kyber/issues/12
    # https://github.com/bigchaindb/js-bigchaindb-driver/blob/master/src/transaction.js
    # https://github.com/planetmint/planetmint-driver-python/blob/main/planetmint_driver/common/transaction.py
    # https://docs.bigchaindb.com/projects/server/en/0.8.2/data-models/crypto-conditions.html
    # https://github.com/bigchaindb/BEPs/tree/master/13#transaction-components-transaction-id

    # Create subfulfillments
    alice_ed25519 = Ed25519Sha256(public_key=base58.b58decode(alice.public_key))
    bob_ed25519 = Ed25519Sha256(public_key=base58.b58decode(bob.public_key))
    carol_ed25519 = Ed25519Sha256(public_key=base58.b58decode(carol.public_key))

    # Create threshold condition (2/3) and add subfulfillments
    threshold_sha256 = ThresholdSha256(2)
    threshold_sha256.add_subfulfillment(alice_ed25519)
    threshold_sha256.add_subfulfillment(bob_ed25519)
    threshold_sha256.add_subfulfillment(carol_ed25519)

    condition_uri = threshold_sha256.condition.serialize_uri()

    condition_details = {
        'subconditions': [
            {'type': s['body'].TYPE_NAME,
            'public_key': base58.b58encode(s['body'].public_key).decode()}
            for s in threshold_sha256.subconditions
            if (s['type'] == 'fulfillment' and
                s['body'].TYPE_NAME == 'ed25519-sha-256')
        ],
        'threshold': threshold_sha256.threshold,
        'type': threshold_sha256.TYPE_NAME,
    }

    output = {
        'amount': '1',
        'condition': {
            'details': condition_details,
            'uri': condition_uri,
        },
        'public_keys': (alice.public_key, bob.public_key, carol.public_key),
    }

    # The yet to be fulfilled input:
    input_ = {
        'fulfillment': None,
        'fulfills': None,
        'owners_before': (alice.public_key,),
    }

    handcrafted_dw_tx = {
        'operation': 'CREATE',
        'asset': dw_asset,
        'metadata': None,
        'outputs': (output,),
        'inputs': (input_,),
        'version': '2.0',
        'id': None,
    }

    message = json.dumps(
        handcrafted_dw_tx,
        sort_keys=True,
        separators=(',', ':'),
        ensure_ascii=False,
    )

    message = sha3.sha3_256(message.encode())

    alice_ed25519.sign(message.digest(), base58.b58decode(alice.private_key))
    bob_ed25519.sign(message.digest(), base58.b58decode(bob.private_key))

    alice_fulfillment_uri = alice_ed25519.serialize_uri()
    bob_fulfillment_uri = bob_ed25519.serialize_uri()

    handcrafted_dw_tx['inputs'][0]['fulfillment'] = alice_fulfillment_uri
    handcrafted_dw_tx['inputs'][1]['fulfillment'] = bob_fulfillment_uri

    json_str_tx = json.dumps(
        handcrafted_dw_tx,
        sort_keys=True,
        separators=(',', ':'),
        ensure_ascii=False,
    )

    dw_creation_txid = sha3.sha3_256(json_str_tx.encode()).hexdigest()

    handcrafted_dw_tx['id'] = dw_creation_txid

    pm.send_commit(handcrafted_dw_tx)

    time.sleep(1)

    hosts.assert_transaction(dw_creation_txid)