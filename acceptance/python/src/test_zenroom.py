import os
import json
import base58
from hashlib import sha3_256
from cryptoconditions.types.ed25519 import Ed25519Sha256
from cryptoconditions.types.zenroom import ZenroomSha256
from planetmint_driver import Planetmint
from planetmint_driver.crypto import generate_keypair





def test_zenroom_signing(gen_key_zencode, secret_key_to_private_key_zencode,
                         fulfill_script_zencode, zenroom_data, zenroom_house_assets,
                         condition_script_zencode):

    biolabs = generate_keypair()
    version = '2.0'

    alice = json.loads(ZenroomSha256.run_zenroom(gen_key_zencode).output)['keyring']
    bob = json.loads(ZenroomSha256.run_zenroom(gen_key_zencode).output)['keyring']

    zen_public_keys = json.loads(ZenroomSha256.run_zenroom(secret_key_to_private_key_zencode.format('Alice'),
                                                keys={'keyring': alice}).output)
    zen_public_keys.update(json.loads(ZenroomSha256.run_zenroom(secret_key_to_private_key_zencode.format('Bob'),
                                                keys={'keyring': bob}).output))



    zenroomscpt = ZenroomSha256(script=fulfill_script_zencode, data=zenroom_data, keys=zen_public_keys)
    print(F'zenroom is: {zenroomscpt.script}')
    
    # CRYPTO-CONDITIONS: generate the condition uri
    condition_uri_zen = zenroomscpt.condition.serialize_uri()    
    print(F'\nzenroom condition URI: {condition_uri_zen}')

    # CRYPTO-CONDITIONS: construct an unsigned fulfillment dictionary
    unsigned_fulfillment_dict_zen = {
        'type': zenroomscpt.TYPE_NAME,
        'public_key': base58.b58encode(biolabs.public_key).decode(),
    }
    output = {
        'amount': '10',
        'condition': {
            'details': unsigned_fulfillment_dict_zen,
            'uri': condition_uri_zen,

        },
        'public_keys': [biolabs.public_key,],
    }
    input_ = {
        'fulfillment': None,
        'fulfills': None,
        'owners_before': [biolabs.public_key,]
    }
    token_creation_tx = {
        'operation': 'CREATE',
        'asset': zenroom_house_assets,
        'metadata': None,
        'outputs': [output,],
        'inputs': [input_,],
        'version': version,
        'id': None,
    }

    # JSON: serialize the transaction-without-id to a json formatted string
    message = json.dumps(
        token_creation_tx,
        sort_keys=True,
        separators=(',', ':'),
        ensure_ascii=False,
    )

    # major workflow:
    # we store the fulfill script in the transaction/message (zenroom-sha)
    # the condition script is used to fulfill the transaction and create the signature
    # 
    # the server should ick the fulfill script and recreate the zenroom-sha and verify the signature

    
    
    message = zenroomscpt.sign(message, condition_script_zencode, alice)
    assert(zenroomscpt.validate(message=message))

    message = json.loads(message)
    fulfillment_uri_zen = zenroomscpt.serialize_uri()
    
    message['inputs'][0]['fulfillment'] = fulfillment_uri_zen
    tx = message
    tx['id'] = None
    json_str_tx = json.dumps(
        tx,
        sort_keys=True,
        skipkeys=False,
        separators=(',', ':')
    )
    # SHA3: hash the serialized id-less transaction to generate the id
    shared_creation_txid = sha3_256(json_str_tx.encode()).hexdigest()
    message['id'] = shared_creation_txid


    # `https://example.com:9984`
    plntmnt = Planetmint(os.environ.get('PLANETMINT_ENDPOINT'))    
    sent_transfer_tx = plntmnt.transactions.send_commit(message)

    print( f"\n\nstatus and result : + {sent_transfer_tx}")    
