import pytest
import json
import base58
from hashlib import sha3_256
from zenroom import zencode_exec
from cryptoconditions.types.ed25519 import Ed25519Sha256
from cryptoconditions.types.zenroom import ZenroomSha256
from planetmint.transactions.common.crypto import generate_key_pair

CONDITION_SCRIPT = """
    Scenario 'ecdh': create the signature of an object
    Given I have the 'keyring'
    Given that I have a 'string dictionary' named 'houses' inside 'asset'
    When I create the signature of 'houses'
    Then print the 'signature'"""

FULFILL_SCRIPT = """Scenario 'ecdh': Bob verifies the signature from Alice
    Given I have a 'ecdh public key' from 'Alice'
    Given that I have a 'string dictionary' named 'houses' inside 'asset'
    Given I have a 'signature' named 'signature' inside 'metadata'
    When I verify the 'houses' has a signature in 'signature' by 'Alice'
    Then print the string 'ok'"""

SK_TO_PK = """Scenario 'ecdh': Create the keypair
    Given that I am known as '{}'
    Given I have the 'keyring'
    When I create the ecdh public key
    When I create the bitcoin address
    Then print my 'ecdh public key'
    Then print my 'bitcoin address'"""

GENERATE_KEYPAIR = """Scenario 'ecdh': Create the keypair
    Given that I am known as 'Pippo'
    When I create the ecdh key
    When I create the bitcoin key
    Then print data"""

ZENROOM_DATA = {"also": "more data"}

HOUSE_ASSETS = {
    "data": {
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
}

metadata = {"units": 300, "type": "KG"}


def test_zenroom_signing():

    biolabs = generate_key_pair()
    version = "2.0"

    alice = json.loads(zencode_exec(GENERATE_KEYPAIR).output)["keyring"]
    bob = json.loads(zencode_exec(GENERATE_KEYPAIR).output)["keyring"]

    zen_public_keys = json.loads(
        zencode_exec(
            SK_TO_PK.format("Alice"), keys=json.dumps({"keyring": alice})
        ).output
    )
    zen_public_keys.update(
        json.loads(
            zencode_exec(
                SK_TO_PK.format("Bob"), keys=json.dumps({"keyring": bob})
            ).output
        )
    )

    zenroomscpt = ZenroomSha256(
        script=FULFILL_SCRIPT, data=ZENROOM_DATA, keys=zen_public_keys
    )
    print(f"zenroom is: {zenroomscpt.script}")

    # CRYPTO-CONDITIONS: generate the condition uri
    condition_uri_zen = zenroomscpt.condition.serialize_uri()
    print(f"\nzenroom condition URI: {condition_uri_zen}")

    # CRYPTO-CONDITIONS: construct an unsigned fulfillment dictionary
    unsigned_fulfillment_dict_zen = {
        "type": zenroomscpt.TYPE_NAME,
        "public_key": base58.b58encode(biolabs.public_key).decode(),
    }
    output = {
        "amount": "10",
        "condition": {
            "details": unsigned_fulfillment_dict_zen,
            "uri": condition_uri_zen,
        },
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
    metadata = {
        "result": {
            "output": ["ok"]
        }
    }
    token_creation_tx = {
        "operation": "CREATE",
        "asset": HOUSE_ASSETS,
        "metadata": metadata,
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
    message = json.dumps(
        token_creation_tx,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )

    # major workflow:
    # we store the fulfill script in the transaction/message (zenroom-sha)
    # the condition script is used to fulfill the transaction and create the signature
    #
    # the server should ick the fulfill script and recreate the zenroom-sha and verify the signature

    message = zenroomscpt.sign(message, CONDITION_SCRIPT, alice)
    assert zenroomscpt.validate(message=message)

    message = json.loads(message)
    fulfillment_uri_zen = zenroomscpt.serialize_uri()

    message["inputs"][0]["fulfillment"] = fulfillment_uri_zen
    tx = message
    tx["id"] = None
    json_str_tx = json.dumps(tx, sort_keys=True, skipkeys=False, separators=(",", ":"))
    # SHA3: hash the serialized id-less transaction to generate the id
    shared_creation_txid = sha3_256(json_str_tx.encode()).hexdigest()
    message["id"] = shared_creation_txid

    from planetmint.models import Transaction
    from planetmint.transactions.common.exceptions import (
        SchemaValidationError,
        ValidationError,
    )

    try:
        tx_obj = Transaction.from_dict(message)
    except SchemaValidationError:
        assert ()
    except ValidationError as e:
        print(e)
        assert ()

    print(f"VALIDATED : {tx_obj}")
    assert (tx_obj == False) is False
