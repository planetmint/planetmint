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

    # Create subfulfillments
    alice_ed25519 = Ed25519Sha256(public_key=base58.b58decode(alice.public_key))
    bob_ed25519 = Ed25519Sha256(public_key=base58.b58decode(bob.public_key))
    carol_ed25519 = Ed25519Sha256(public_key=base58.b58decode(carol.public_key))

    # Create threshold condition (2/3) and add subfulfillments
    threshold_sha256 = ThresholdSha256(2)
    threshold_sha256.add_subfulfillment(alice_ed25519)
    threshold_sha256.add_subfulfillment(bob_ed25519)
    threshold_sha256.add_subfulfillment(carol_ed25519)

    # Create a condition uri and details for the output object
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

    # Assemble output and input for the handcrafted tx
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
        'owners_before': (alice.public_key, bob.public_key),
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

    fulfillment_threshold = ThresholdSha256(2)
    fulfillment_threshold.add_subfulfillment(alice_ed25519)
    fulfillment_threshold.add_subfulfillment(bob_ed25519)
    fulfillment_threshold.add_subcondition(carol_ed25519.condition)

    fulfillment_uri = fulfillment_threshold.serialize_uri()

    handcrafted_dw_tx['inputs'][0]['fulfillment'] = fulfillment_uri

    json_str_tx = json.dumps(
        handcrafted_dw_tx,
        sort_keys=True,
        separators=(',', ':'),
        ensure_ascii=False,
    )

    dw_creation_txid = sha3.sha3_256(json_str_tx.encode()).hexdigest()

    handcrafted_dw_tx['id'] = dw_creation_txid

    pm.transactions.send_commit(handcrafted_dw_tx)

    time.sleep(1)

    hosts.assert_transaction(dw_creation_txid)