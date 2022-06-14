import pytest
import json
import base58
from hashlib import sha3_256
import cryptoconditions as cc
from cryptoconditions.types.ed25519 import Ed25519Sha256
from cryptoconditions.types.zenroom import ZenroomSha256
from cryptoconditions.crypto import Ed25519SigningKey as SigningKey
from nacl.signing import VerifyKey
from planetmint_driver.crypto import generate_keypair

import zenroom

CONDITION_SCRIPT = """Rule input encoding base58
    Rule output encoding base58
    Scenario 'ecdh': create the signature of an object
    Given I have the 'keys'
    Given that I have a 'string dictionary' named 'houses' inside 'asset'
    When I create the signature of 'houses'
    When I rename the 'signature' to 'data.signature'
    Then print the 'data.signature'"""
    
FULFILL_SCRIPT = \
    """Rule input encoding base58
    Rule output encoding base58
    Scenario 'ecdh': Bob verifies the signature from Alice
    Given I have a 'ecdh public key' from 'Alice'
    Given that I have a 'string dictionary' named 'houses' inside 'asset'
    Given I have a 'signature' named 'data.signature' inside 'result'
    When I verify the 'houses' has a signature in 'data.signature' by 'Alice'
    Then print the string 'ok'"""
    
SK_TO_PK = \
    """Rule input encoding base58
    Rule output encoding base58
    Scenario 'ecdh': Create the keypair
    Given that I am known as '{}'
    Given I have the 'keys'
    When I create the ecdh public key
    When I create the testnet address
    Then print my 'ecdh public key'
    Then print my 'testnet address'"""

GENERATE_KEYPAIR = \
    """Rule input encoding base58
    Rule output encoding base58
    Scenario 'ecdh': Create the keypair
    Given that I am known as 'Pippo'
    When I create the ecdh key
    When I create the testnet key
    Then print data"""

ZENROOM_DATA = {
    'also': 'more data'
}
#bdb_root_url = 'https://ipdb3.riddleandcode.com'

def test_manual_tx_crafting():
    
    producer, buyer, reseller = generate_keypair(), generate_keypair(), generate_keypair()
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
                }
            ],
        }
    }

    metadata = {
        'units': 300,
        'type': 'KG'
    }
    


    from planetmint_driver import Planetmint as plntmnt_p
    server = 'https://test.ipdb.io'
    api = 'api/v1/transactions'
    plmnt = plntmnt_p(server)

    prepared_token_tx = plmnt.transactions.prepare(
                operation='CREATE',
                signers=producer.public_key,
                recipients=[([producer.public_key], 3000)],
                asset=HOUSE_ASSETS,
                metadata=metadata)

    print( f"prepared: {prepared_token_tx}")
    signed_asset_creation = plmnt.transactions.fulfill(
                prepared_token_tx,
                private_keys=producer.private_key)
    print( f"signed: {signed_asset_creation}")


    from planetmint.models import Transaction
    from planetmint.transactions.common.exceptions import SchemaValidationError, ValidationError
    validated = None
    try:
        tx_obj = Transaction.from_dict(signed_asset_creation)
    except SchemaValidationError as e:
        assert()
    except ValidationError as e:
        print(e)
        assert()

    from planetmint.lib import Planetmint
    planet = Planetmint()
    validated = planet.validate_transaction(tx_obj)
    print( f"\n\nVALIDATED =====: {validated}")
    assert not validated == False

def test_manual_tx_crafting_ext():
    
    producer, buyer, reseller = generate_keypair(), generate_keypair(), generate_keypair()
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
                }
            ],
        }
    }

    metadata = {
        'units': 300,
        'type': 'KG'
    }
    producer_ed25519 = Ed25519Sha256(public_key=base58.b58decode(producer.public_key))
    condition_uri = producer_ed25519.condition.serialize_uri()
    output = {
        'amount': '3000',
        'condition': {
            'details': {
              "type": "ed25519-sha-256",
              "public_key": producer.public_key      
            },
            'uri': condition_uri,

        },
        'public_keys': [producer.public_key,],
    }
    input_ = {
        'fulfillment': None,
        'fulfills': None,
        'owners_before': [producer.public_key,]
    }
    version = '2.0'
    from planetmint_driver import Planetmint as plntmnt_p
    server = 'https://test.ipdb.io'
    api = 'api/v1/transactions'
    plmnt = plntmnt_p(server)

    prepared_token_tx = {
        'operation': 'CREATE',
        'asset': HOUSE_ASSETS,#rfid_token,
        'metadata': metadata,
        'outputs': [output,],
        'inputs': [input_,],
        'version': version,
        'id': None,
    }

    print( f"prepared: {prepared_token_tx}")
    
        # Create sha3-256 of message to sign
    message = json.dumps(
        prepared_token_tx,
        sort_keys=True,
        separators=(',', ':'),
        ensure_ascii=False,
    )
    message_hash = sha3_256(message.encode())
    
    producer_ed25519.sign(message_hash.digest(), base58.b58decode(producer.private_key))
    
    fulfillment_uri = producer_ed25519.serialize_uri()

    prepared_token_tx['inputs'][0]['fulfillment'] = fulfillment_uri
    
    json_str_tx = json.dumps(
        prepared_token_tx,
        sort_keys=True,
        separators=(',', ':'),
        ensure_ascii=False,
    )
    creation_txid = sha3_256(json_str_tx.encode()).hexdigest()

    prepared_token_tx['id'] = creation_txid

    print( f"signed: {prepared_token_tx}")

    from planetmint.transactions.types.assets.create import Create
    from planetmint.transactions.types.assets.transfer import Transfer
    from planetmint.models import Transaction
    from planetmint.transactions.common.exceptions import SchemaValidationError, ValidationError
    from flask import current_app
    from planetmint.transactions.common.transaction_mode_types import BROADCAST_TX_ASYNC
    validated = None
    try:
        tx_obj = Transaction.from_dict(prepared_token_tx)
    except SchemaValidationError as e:
        assert()
    except ValidationError as e:
        print(e)
        assert()

    from planetmint.lib import Planetmint
    planet = Planetmint()
    validated = planet.validate_transaction(tx_obj)
    print( f"\n\nVALIDATED =====: {validated}")
    assert not validated == False

def test_manual_tx_crafting_ext_zenroom():
    
    producer= generate_keypair()
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
                }
            ],
        }
    }

    metadata = {
        'units': 300,
        'type': 'KG'
    }
    producer_ed25519 = Ed25519Sha256(public_key=base58.b58decode(producer.public_key))
    condition_uri = producer_ed25519.condition.serialize_uri()
    output = {
        'amount': '3000',
        'condition': {
            'details': {
              "type": "ed25519-sha-256",
              "public_key": producer.public_key      
            },
            'uri': condition_uri,

        },
        'public_keys': [producer.public_key,],
    }
    input_ = {
        'fulfillment': None,
        'fulfills': None,
        'owners_before': [producer.public_key,]
    }
    version = '2.0'
    from planetmint_driver import Planetmint as plntmnt_p
    server = 'https://test.ipdb.io'
    api = 'api/v1/transactions'
    plmnt = plntmnt_p(server)

    prepared_token_tx = {
        'operation': 'CREATE',
        'asset': HOUSE_ASSETS,#rfid_token,
        'metadata': metadata,
        'outputs': [output,],
        'inputs': [input_,],
        'version': version,
        'id': None,
    }

    print( f"prepared: {prepared_token_tx}")
    
        # Create sha3-256 of message to sign
    message = json.dumps(
        prepared_token_tx,
        sort_keys=True,
        separators=(',', ':'),
        ensure_ascii=False,
    )
    message_hash = sha3_256(message.encode())
    
    producer_ed25519.sign(message_hash.digest(), base58.b58decode(producer.private_key))
    
    fulfillment_uri = producer_ed25519.serialize_uri()

    prepared_token_tx['inputs'][0]['fulfillment'] = fulfillment_uri
    
    json_str_tx = json.dumps(
        prepared_token_tx,
        sort_keys=True,
        separators=(',', ':'),
        ensure_ascii=False,
    )
    creation_txid = sha3_256(json_str_tx.encode()).hexdigest()

    prepared_token_tx['id'] = creation_txid

    print( f"signed: {prepared_token_tx}")

    from planetmint.transactions.types.assets.create import Create
    from planetmint.transactions.types.assets.transfer import Transfer
    from planetmint.models import Transaction
    from planetmint.transactions.common.exceptions import SchemaValidationError, ValidationError
    from flask import current_app
    from planetmint.transactions.common.transaction_mode_types import BROADCAST_TX_ASYNC
    validated = None
    try:
        tx_obj = Transaction.from_dict(prepared_token_tx)
    except SchemaValidationError as e:
        assert()
    except ValidationError as e:
        print(e)
        assert()

    from planetmint.lib import Planetmint
    planet = Planetmint()
    validated = planet.validate_transaction(tx_obj)
    print( f"\n\nVALIDATED =====: {validated}")
    assert not validated == False

def test_zenroom_signing():
#    bdb_root_url = 'http://localhost:9984/'
#    bdb = Planetmint(bdb_root_url)

    # generate the keypairs/wallets for biolabs and the hospital
    # the pacemaker will only e represented by its public key address
    # derived from the attached RFID tag's EPC code


    biolabs, hospital = generate_keypair(), generate_keypair()
    
    print(biolabs.private_key)
    print(biolabs.public_key)
    print(hospital.private_key)
    print(hospital.public_key)
    print('\n\n\n')
    # biolabs = CryptoKeypair(private_key='2KF5Qx4ksFWQ7j7DgTj1jYhQ6eoP38WoyFVMjTR5hDgK', public_key='2KF5Qx4ksFWQ7j7DgTj1jYhQ6eoP38WoyFVMjTR5hDgK')
    # print(biolabs.private_key)
    # hospital = CryptoKeypair(private_key='ASHwLY9zG43rNkCZgRFBV6K9j9oHM1joxYMxHRiNyPja', public_key='A7fpfDpaGkJubquXbj3cssMhx5GQ1599Sxc7MxR9SWa8')
    # create a digital asset for biolabs
    # for readability we turn the original EPC code into capital hex chars
#    rfid_token = {
#        'data': {
#            'token_for': {
#                'UCODE_DNA': {
#                    'EPC_serial_number': 'E2003787C9AE8209161AF72F',
#                    'amount_issued': 100,
#                    'pegged_to'    : 'SFR',
#                    #'pub_key'      : elements.public_key,
#                }
#            },
#            #'description': 'Biolab\'s blockchain settlement system for pacemakers.',
#        },
#    }
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
                }
            ],
        }
}
    version = '2.0'

    CONDITION_SCRIPT = """Rule input encoding base58
        Rule output encoding base58
        Scenario 'ecdh': create the signature of an object
        Given I have the 'keys'
        Given that I have a 'string dictionary' named 'houses' inside 'asset'
        When I create the signature of 'houses'
        When I rename the 'signature' to 'data.signature'
        Then print the 'data.signature'"""
        
    FULFILL_SCRIPT = \
        """Rule input encoding base58
        Rule output encoding base58
        Scenario 'ecdh': Bob verifies the signature from Alice
        Given I have a 'ecdh public key' from 'Alice'
        Given that I have a 'string dictionary' named 'houses' inside 'asset'
        Given I have a 'signature' named 'data.signature' inside 'result'
        When I verify the 'houses' has a signature in 'data.signature' by 'Alice'
        Then print the string 'ok'"""
        
    SK_TO_PK = \
        """Rule input encoding base58
        Rule output encoding base58
        Scenario 'ecdh': Create the keypair
        Given that I am known as '{}'
        Given I have the 'keys'
        When I create the ecdh public key
        When I create the testnet address
        Then print my 'ecdh public key'
        Then print my 'testnet address'"""

    GENERATE_KEYPAIR = \
        """Rule input encoding base58
        Rule output encoding base58
        Scenario 'ecdh': Create the keypair
        Given that I am known as 'Pippo'
        When I create the ecdh key
        When I create the testnet key
        Then print data"""

    ZENROOM_DATA = {
        'also': 'more data'
    }
    alice = json.loads(ZenroomSha256.run_zenroom(GENERATE_KEYPAIR).output)['keys']
    bob = json.loads(ZenroomSha256.run_zenroom(GENERATE_KEYPAIR).output)['keys']

    zen_public_keys = json.loads(ZenroomSha256.run_zenroom(SK_TO_PK.format('Alice'),
                                                keys={'keys': alice}).output)
    zen_public_keys.update(json.loads(ZenroomSha256.run_zenroom(SK_TO_PK.format('Bob'),
                                                keys={'keys': bob}).output))



    zenroomscpt = ZenroomSha256(script=FULFILL_SCRIPT, data=ZENROOM_DATA, keys=zen_public_keys)
    print(F'zenroom is: {zenroomscpt.script}')
    
    # CRYPTO-CONDITIONS: generate the condition uri
    condition_uri_zen = zenroomscpt.condition.serialize_uri()    
    print(F'\nzenroom condition URI: {condition_uri_zen}')
    #print(F'condition_uri is: {condition_uri}')
    # # print(F'condition_uri_zen is: {condition_uri_zen}')
    # ZEN-CRYPTO-CONDITION: generate the condition did
    #zen_condition_did = 'did:bdb:MIIBMxaCARoKICAgIC0tIGdlbmVyYXRlIGEgc2ltcGxlIGtleXJpbmcKICAgIGtleXJpbmcgPSBFQ0RILm5ldygpCiAgICBrZXlyaW5nOmtleWdlbigpCiAgICAKICAgIC0tIGV4cG9ydCB0aGUga2V5cGFpciB0byBqc29uCiAgICBleHBvcnQgPSBKU09OLmVuY29kZSgKICAgICAgIHsKICAgICAgICAgIHB1YmxpYyAgPSBrZXlyaW5nOiBwdWJsaWMoKTpiYXNlNjQoKSwKICAgICAgICAgIHByaXZhdGUgPSBrZXlyaW5nOnByaXZhdGUoKTpiYXNlNjQoKQogICAgICAgfQogICAgKQogICAgcHJpbnQoZXhwb3J0KQoWBE5vbmUWBE5vbmUWBE5vbmUCAQA='
    
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
        'asset': HOUSE_ASSETS,#rfid_token,
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

    
    
    message = zenroomscpt.sign(message, CONDITION_SCRIPT, alice)
    assert(zenroomscpt.validate(message=message))

    ### WORkS until here
    
    

    fulfillment_uri_zen = zenroomscpt.serialize_uri()
    print(f'\nfulfillment_uri_zen is: {fulfillment_uri_zen}')
    fulfillment_fromuri_zen = zenroomscpt.from_uri(fulfillment_uri_zen)
    token_creation_tx['inputs'][0]['fulfillment'] = fulfillment_uri_zen
    tx = token_creation_tx
    tx['id'] = None
    json_str_tx = json.dumps(
        tx,
        sort_keys=True,
        skipkeys=False,
        separators=(',', ':')
    )
    # SHA3: hash the serialized id-less transaction to generate the id
    shared_creation_txid = sha3_256(json_str_tx.encode()).hexdigest()
    # add the id
    token_creation_tx['id'] = shared_creation_txid
    #print(F'The TX to be consensed: {token_creation_tx}')
    # send CREATE tx into the bdb network
    ##tx = signed_create_tx.to_dict()
    ##tx['id'] = None
    ##payload = json.dumps(tx, skipkeys=False, sort_keys=True,
    ##                     separators=(',', ':'))
    ##assert sha3_256(payload.encode()).hexdigest() == signed_create_tx.id
    
    #returned_creation_tx = bdb.transactions.send_commit(token_creation_tx)    
    #tx = request.get_json(force=True)

    from planetmint.transactions.types.assets.create import Create
    from planetmint.transactions.types.assets.transfer import Transfer
    from planetmint.models import Transaction
    from planetmint.transactions.common.exceptions import SchemaValidationError, ValidationError
    from flask import current_app
    from planetmint.transactions.common.transaction_mode_types import BROADCAST_TX_ASYNC
    validated = None
    try:
        tx_obj = Transaction.from_dict(token_creation_tx)
    except SchemaValidationError as e:
        assert()
    except ValidationError as e:
        print(e)
        assert()
    #pool = current_app.config['bigchain_pool']
    #with pool() as planet:
    #try:
    from planetmint.lib import Planetmint
    planet = Planetmint()
    validated = planet.validate_transaction(tx_obj)
    print( f"\n\nVALIDATED =====: {validated}")
    #except ValidationError as e:
    #    assert()
    mode = BROADCAST_TX_ASYNC
    status_code, message = planet.write_transaction(tx_obj, mode)
    print( f"\n\nstatus and result : {status_code} + {message}")
    print( f"VALIDATED : {validated}")
    assert()
    
