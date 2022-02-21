# GOAL:
# In this script I tried to implement the ECDSA signature using zenroom

# However, the scripts are customizable and so with the same procedure
# we can implement more complex smart contracts

# PUBLIC IDENTITY
# The public identity of the users in this script (Bob and Alice)
# is the pair (ECDH public key, Testnet address)

import json

import hashlib
from cryptoconditions import ZenroomSha256
from json.decoder import JSONDecodeError

def test_zenroom(gen_key_zencode, secret_key_to_private_key_zencode, fulfill_script_zencode, 
condition_script_zencode, zenroom_data, zenroom_house_assets):
    alice = json.loads(ZenroomSha256.run_zenroom(gen_key_zencode).output)['keys']
    bob = json.loads(ZenroomSha256.run_zenroom(gen_key_zencode).output)['keys']

    zen_public_keys = json.loads(ZenroomSha256.run_zenroom(secret_key_to_private_key_zencode.format('Alice'),
                                                keys={'keys': alice}).output)
    zen_public_keys.update(json.loads(ZenroomSha256.run_zenroom(secret_key_to_private_key_zencode.format('Bob'),
                                                keys={'keys': bob}).output))

    # CRYPTO-CONDITIONS: instantiate an Ed25519 crypto-condition for buyer
    zenSha = ZenroomSha256(script=fulfill_script_zencode, keys=zen_public_keys, data=zenroom_data)

    # CRYPTO-CONDITIONS: generate the condition uri
    condition_uri = zenSha.condition.serialize_uri()

    # CRYPTO-CONDITIONS: construct an unsigned fulfillment dictionary
    unsigned_fulfillment_dict = {
        'type': zenSha.TYPE_NAME,
        'script': fulfill_script_zencode,
        'keys': zen_public_keys,
    }

    output = {
        'amount': '1000',
        'condition': {
            'details': unsigned_fulfillment_dict,
            'uri': condition_uri,
        },
        'data': zenroom_data,
        'script': fulfill_script_zencode,
        'conf': '',
        'public_keys': (zen_public_keys['Alice']['ecdh_public_key'], ),
    }


    input_ = {
        'fulfillment': None,
        'fulfills': None,
        'owners_before': (zen_public_keys['Alice']['ecdh_public_key'], ),
    }

    token_creation_tx = {
        'operation': 'CREATE',
        'asset': zenroom_house_assets,
        'metadata': None,
        'outputs': (output,),
        'inputs': (input_,),
        'version': '2.0',
        'id': None,
    }

    # JSON: serialize the transaction-without-id to a json formatted string
    message = json.dumps(
        token_creation_tx,
        sort_keys=True,
        separators=(',', ':'),
        ensure_ascii=False,
    )

    try:
        assert(not zenSha.validate(message=message))
    except JSONDecodeError:
        pass
    except ValueError:
        pass

    message = zenSha.sign(message, condition_script_zencode, alice)
    assert(zenSha.validate(message=message))
