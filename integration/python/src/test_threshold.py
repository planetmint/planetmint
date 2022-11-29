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
from planetmint_cryptoconditions import Ed25519Sha256, ThresholdSha256
from planetmint_driver.crypto import generate_keypair

# Import helper to deal with multiple nodes
from .helper.hosts import Hosts


def prepare_condition_details(condition: ThresholdSha256):
    condition_details = {"subconditions": [], "threshold": condition.threshold, "type": condition.TYPE_NAME}

    for s in condition.subconditions:
        if s["type"] == "fulfillment" and s["body"].TYPE_NAME == "ed25519-sha-256":
            condition_details["subconditions"].append(
                {"type": s["body"].TYPE_NAME, "public_key": base58.b58encode(s["body"].public_key).decode()}
            )
        else:
            condition_details["subconditions"].append(prepare_condition_details(s["body"]))

    return condition_details


def test_threshold():
    # Setup connection to test nodes
    hosts = Hosts("/shared/hostnames")
    pm = hosts.get_connection()

    # Generate Keypars for Alice, Bob an Carol!
    alice, bob, carol = generate_keypair(), generate_keypair(), generate_keypair()

    # ## Alice and Bob create a transaction
    # Alice and Bob just moved into a shared flat, no one can afford these
    # high rents anymore. Bob suggests to get a dish washer for the
    # kitchen. Alice agrees and here they go, creating the asset for their
    # dish washer.
    dw_asset = [{"data": {"dish washer": {"serial_number": 1337}}}]

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
    condition_details = prepare_condition_details(threshold_sha256)

    # Assemble output and input for the handcrafted tx
    output = {
        "amount": "1",
        "condition": {
            "details": condition_details,
            "uri": condition_uri,
        },
        "public_keys": (alice.public_key, bob.public_key, carol.public_key),
    }

    # The yet to be fulfilled input:
    input_ = {
        "fulfillment": None,
        "fulfills": None,
        "owners_before": (alice.public_key, bob.public_key),
    }

    # Assemble the handcrafted transaction
    handcrafted_dw_tx = {
        "operation": "CREATE",
        "asset": dw_asset,
        "metadata": None,
        "outputs": (output,),
        "inputs": (input_,),
        "version": "2.0",
        "id": None,
    }

    # Create sha3-256 of message to sign
    message = json.dumps(
        handcrafted_dw_tx,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )
    message = sha3.sha3_256(message.encode())

    # Sign message with Alice's und Bob's private key
    alice_ed25519.sign(message.digest(), base58.b58decode(alice.private_key))
    bob_ed25519.sign(message.digest(), base58.b58decode(bob.private_key))

    # Create fulfillment and add uri to inputs
    fulfillment_threshold = ThresholdSha256(2)
    fulfillment_threshold.add_subfulfillment(alice_ed25519)
    fulfillment_threshold.add_subfulfillment(bob_ed25519)
    fulfillment_threshold.add_subcondition(carol_ed25519.condition)

    fulfillment_uri = fulfillment_threshold.serialize_uri()

    handcrafted_dw_tx["inputs"][0]["fulfillment"] = fulfillment_uri

    # Create tx_id for handcrafted_dw_tx and send tx commit
    json_str_tx = json.dumps(
        handcrafted_dw_tx,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )

    dw_creation_txid = sha3.sha3_256(json_str_tx.encode()).hexdigest()

    handcrafted_dw_tx["id"] = dw_creation_txid

    pm.transactions.send_commit(handcrafted_dw_tx)

    time.sleep(1)

    # Assert that the tx is propagated to all nodes
    hosts.assert_transaction(dw_creation_txid)


def test_weighted_threshold():
    hosts = Hosts("/shared/hostnames")
    pm = hosts.get_connection()

    alice, bob, carol = generate_keypair(), generate_keypair(), generate_keypair()

    assets = [{"data": {"trashcan": {"animals": ["racoon_1", "racoon_2"]}}}]

    alice_ed25519 = Ed25519Sha256(public_key=base58.b58decode(alice.public_key))
    bob_ed25519 = Ed25519Sha256(public_key=base58.b58decode(bob.public_key))
    carol_ed25519 = Ed25519Sha256(public_key=base58.b58decode(carol.public_key))

    threshold = ThresholdSha256(1)
    threshold.add_subfulfillment(alice_ed25519)

    sub_threshold = ThresholdSha256(2)
    sub_threshold.add_subfulfillment(bob_ed25519)
    sub_threshold.add_subfulfillment(carol_ed25519)

    threshold.add_subfulfillment(sub_threshold)

    condition_uri = threshold.condition.serialize_uri()
    condition_details = prepare_condition_details(threshold)

    # Assemble output and input for the handcrafted tx
    output = {
        "amount": "1",
        "condition": {
            "details": condition_details,
            "uri": condition_uri,
        },
        "public_keys": (alice.public_key, bob.public_key, carol.public_key),
    }

    # The yet to be fulfilled input:
    input_ = {
        "fulfillment": None,
        "fulfills": None,
        "owners_before": (alice.public_key, bob.public_key),
    }

    # Assemble the handcrafted transaction
    handcrafted_tx = {
        "operation": "CREATE",
        "asset": assets,
        "metadata": None,
        "outputs": (output,),
        "inputs": (input_,),
        "version": "2.0",
        "id": None,
    }

    # Create sha3-256 of message to sign
    message = json.dumps(
        handcrafted_tx,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )
    message = sha3.sha3_256(message.encode())

    # Sign message with Alice's und Bob's private key
    alice_ed25519.sign(message.digest(), base58.b58decode(alice.private_key))

    # Create fulfillment and add uri to inputs
    sub_fulfillment_threshold = ThresholdSha256(2)
    sub_fulfillment_threshold.add_subcondition(bob_ed25519.condition)
    sub_fulfillment_threshold.add_subcondition(carol_ed25519.condition)

    fulfillment_threshold = ThresholdSha256(1)
    fulfillment_threshold.add_subfulfillment(alice_ed25519)
    fulfillment_threshold.add_subfulfillment(sub_fulfillment_threshold)

    fulfillment_uri = fulfillment_threshold.serialize_uri()

    handcrafted_tx["inputs"][0]["fulfillment"] = fulfillment_uri

    # Create tx_id for handcrafted_dw_tx and send tx commit
    json_str_tx = json.dumps(
        handcrafted_tx,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )

    creation_tx_id = sha3.sha3_256(json_str_tx.encode()).hexdigest()

    handcrafted_tx["id"] = creation_tx_id

    pm.transactions.send_commit(handcrafted_tx)

    time.sleep(1)

    # Assert that the tx is propagated to all nodes
    hosts.assert_transaction(creation_tx_id)

    # Now transfer created asset
    alice_transfer_ed25519 = Ed25519Sha256(public_key=base58.b58decode(alice.public_key))
    bob_transfer_ed25519 = Ed25519Sha256(public_key=base58.b58decode(bob.public_key))
    carol_transfer_ed25519 = Ed25519Sha256(public_key=base58.b58decode(carol.public_key))

    transfer_condition_uri = alice_transfer_ed25519.condition.serialize_uri()

    # Assemble output and input for the handcrafted tx
    transfer_output = {
        "amount": "1",
        "condition": {
            "details": {
                "type": alice_transfer_ed25519.TYPE_NAME,
                "public_key": base58.b58encode(alice_transfer_ed25519.public_key).decode(),
            },
            "uri": transfer_condition_uri,
        },
        "public_keys": (alice.public_key,),
    }

    # The yet to be fulfilled input:
    transfer_input_ = {
        "fulfillment": None,
        "fulfills": {"transaction_id": creation_tx_id, "output_index": 0},
        "owners_before": (alice.public_key, bob.public_key, carol.public_key),
    }

    # Assemble the handcrafted transaction
    handcrafted_transfer_tx = {
        "operation": "TRANSFER",
        "assets": [{"id": creation_tx_id}],
        "metadata": None,
        "outputs": (transfer_output,),
        "inputs": (transfer_input_,),
        "version": "2.0",
        "id": None,
    }

    # Create sha3-256 of message to sign
    message = json.dumps(
        handcrafted_transfer_tx,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )
    message = sha3.sha3_256(message.encode())

    message.update(
        "{}{}".format(
            handcrafted_transfer_tx["inputs"][0]["fulfills"]["transaction_id"],
            handcrafted_transfer_tx["inputs"][0]["fulfills"]["output_index"],
        ).encode()
    )

    # Sign message with Alice's und Bob's private key
    bob_transfer_ed25519.sign(message.digest(), base58.b58decode(bob.private_key))
    carol_transfer_ed25519.sign(message.digest(), base58.b58decode(carol.private_key))

    sub_fulfillment_threshold = ThresholdSha256(2)
    sub_fulfillment_threshold.add_subfulfillment(bob_transfer_ed25519)
    sub_fulfillment_threshold.add_subfulfillment(carol_transfer_ed25519)

    # Create fulfillment and add uri to inputs
    fulfillment_threshold = ThresholdSha256(1)
    fulfillment_threshold.add_subcondition(alice_transfer_ed25519.condition)
    fulfillment_threshold.add_subfulfillment(sub_fulfillment_threshold)

    fulfillment_uri = fulfillment_threshold.serialize_uri()

    handcrafted_transfer_tx["inputs"][0]["fulfillment"] = fulfillment_uri

    # Create tx_id for handcrafted_dw_tx and send tx commit
    json_str_tx = json.dumps(
        handcrafted_transfer_tx,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )

    transfer_tx_id = sha3.sha3_256(json_str_tx.encode()).hexdigest()

    handcrafted_transfer_tx["id"] = transfer_tx_id

    pm.transactions.send_commit(handcrafted_transfer_tx)

    time.sleep(1)

    # Assert that the tx is propagated to all nodes
    hosts.assert_transaction(transfer_tx_id)
