import pytest
import json
import base58
from hashlib import sha3_256
from zenroom import zencode_exec
from cryptoconditions.types.ed25519 import Ed25519Sha256
from cryptoconditions.types.zenroom import ZenroomSha256
from planetmint.transactions.common.crypto import generate_key_pair
from ipld import multihash, marshal

CONDITION_SCRIPT = """Scenario 'ecdh': create the signature of an object
    Given I have the 'keyring'
    Given that I have a 'string dictionary' named 'houses'
    When I create the signature of 'houses'
    Then print the 'signature'"""

FULFILL_SCRIPT = """Scenario 'ecdh': Bob verifies the signature from Alice
    Given I have a 'ecdh public key' from 'Alice'
    Given that I have a 'string dictionary' named 'houses'
    Given I have a 'signature' named 'signature'
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

INITIAL_STATE = {"also": "more data"}
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


def test_zenroom_signing():

    biolabs = generate_key_pair()
    version = "2.0"

    alice = json.loads(zencode_exec(GENERATE_KEYPAIR).output)["keyring"]
    bob = json.loads(zencode_exec(GENERATE_KEYPAIR).output)["keyring"]

    zen_public_keys = json.loads(zencode_exec(SK_TO_PK.format("Alice"), keys=json.dumps({"keyring": alice})).output)
    zen_public_keys.update(json.loads(zencode_exec(SK_TO_PK.format("Bob"), keys=json.dumps({"keyring": bob})).output))

    zenroomscpt = ZenroomSha256(script=FULFILL_SCRIPT, data=INITIAL_STATE, keys=zen_public_keys)
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
    script_ = {
        "code": {"type": "zenroom", "raw": "test_string", "parameters": [{"obj": "1"}, {"obj": "2"}]},
        "state": "dd8bbd234f9869cab4cc0b84aa660e9b5ef0664559b8375804ee8dce75b10576",
        "input": SCRIPT_INPUT,
        "output": ["ok"],
        "policies": {},
    }
    metadata = {"result": {"output": ["ok"]}}
    token_creation_tx = {
        "operation": "CREATE",
        "asset": {"data": multihash(marshal({"test": "my asset"}))},
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
    script_ = json.dumps(script_)
    # major workflow:
    # we store the fulfill script in the transaction/message (zenroom-sha)
    # the condition script is used to fulfill the transaction and create the signature
    #
    # the server should ick the fulfill script and recreate the zenroom-sha and verify the signature

    signed_input = zenroomscpt.sign(script_, CONDITION_SCRIPT, alice)

    input_signed = json.loads(signed_input)
    input_signed["input"]["signature"] = input_signed["output"]["signature"]
    del input_signed["output"]["signature"]
    del input_signed["output"]["logs"]
    input_signed["output"] = ["ok"]  # define expected output that is to be compared
    input_msg = json.dumps(input_signed)
    assert zenroomscpt.validate(message=input_msg)

    tx = json.loads(tx)
    fulfillment_uri_zen = zenroomscpt.serialize_uri()

    tx["script"] = input_signed
    tx["inputs"][0]["fulfillment"] = fulfillment_uri_zen
    tx["id"] = None
    json_str_tx = json.dumps(tx, sort_keys=True, skipkeys=False, separators=(",", ":"))
    # SHA3: hash the serialized id-less transaction to generate the id
    shared_creation_txid = sha3_256(json_str_tx.encode()).hexdigest()
    tx["id"] = shared_creation_txid

    from planetmint.transactions.common.transaction import Transaction
    from planetmint.lib import Planetmint
    from planetmint.transactions.common.exceptions import (
        SchemaValidationError,
        ValidationError,
    )

    try:
        print(f"TX\n{tx}")
        tx_obj = Transaction.from_dict(tx, False)
    except SchemaValidationError as e:
        print(e)
        assert ()
    except ValidationError as e:
        print(e)
        assert ()
    planet = Planetmint()
    try:
        planet.validate_transaction(tx_obj)
    except ValidationError as e:
        print("Invalid transaction ({}): {}".format(type(e).__name__, e))
        assert ()

    print(f"VALIDATED : {tx_obj}")
    assert (tx_obj == False) is False
