import json
import base58
import pytest

from hashlib import sha3_256
from planetmint_cryptoconditions.types.ed25519 import Ed25519Sha256
from transactions.common.crypto import generate_key_pair
from transactions.common.utils import _fulfillment_to_details
from ipld import multihash, marshal

INITIAL_STATE = {"also": "more data"}
ZENROOM_SCRIPT = """
    Scenario 'test': Script verifies input
    Given that I have a 'string dictionary' named 'houses'
    Then print the string 'ok'
"""
SCRIPT_INPUT = {
    "houses": [
        {
            "name": "Harry",
            "team": "Gryffindor",
        },
        {
            "name": "Draco",
            "team": "Slytherin",
        },
    ],
}

metadata = {"units": 300, "type": "KG"}

SCRIPT_OUTPUTS = ["ok"]


@pytest.mark.skip(reason="new zenroom adjusteds have to be made")
def test_zenroom_validation(b):
    biolabs = generate_key_pair()
    version = "3.0"

    ed25519 = Ed25519Sha256(public_key=base58.b58decode(biolabs.public_key))

    output = {
        "amount": "10",
        "condition": {"details": _fulfillment_to_details(ed25519), "uri": ed25519.condition_uri},
        "public_keys": [
            biolabs.public_key,
        ],
    }
    input_ = {
        "fulfillment": None,
        "fulfills": None,
        "owners_before": [
            biolabs.public_key,
        ],
    }
    script_ = {
        "code": ZENROOM_SCRIPT,
        "inputs": SCRIPT_INPUT,
        "outputs": SCRIPT_OUTPUTS,
        "state": "dd8bbd234f9869cab4cc0b84aa660e9b5ef0664559b8375804ee8dce75b10576",
        "policies": {},
    }
    metadata = {"result": {"output": ["ok"]}}
    token_creation_tx = {
        "operation": "CREATE",
        "assets": [{"data": multihash(marshal({"test": "my asset"}))}],
        "metadata": multihash(marshal(metadata)),
        "script": script_,
        "outputs": [
            output,
        ],
        "inputs": [
            input_,
        ],
        "version": version,
        "id": None,
    }

    # JSON: serialize the transaction-without-id to a json formatted string
    tx = json.dumps(
        token_creation_tx,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )

    ed25519.sign(message=sha3_256(tx.encode()).digest(), private_key=base58.b58decode(biolabs.private_key))

    tx = json.loads(tx)
    tx["inputs"][0]["fulfillment"] = ed25519.serialize_uri()
    tx["id"] = None
    json_str_tx = json.dumps(tx, sort_keys=True, skipkeys=False, separators=(",", ":"))
    shared_creation_txid = sha3_256(json_str_tx.encode()).hexdigest()
    tx["id"] = shared_creation_txid

    from transactions.common.transaction import Transaction

    tx_obj = Transaction.from_dict(tx, False)
    b.validate_transaction(tx_obj)
    assert (tx_obj == False) is False
