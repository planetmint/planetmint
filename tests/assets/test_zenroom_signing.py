import pytest
import json
import base58
import sha3
import cryptoconditions as cc
from cryptoconditions.types.ed25519 import Ed25519Sha256
from cryptoconditions.types.zenroom import ZenroomSha256
from cryptoconditions.crypto import Ed25519SigningKey as SigningKey
from nacl.signing import VerifyKey

#from zenroom import zenroom
#from zenroom.zenroom import ZenroomException

import zenroom
import lupa
from lupa import LuaRuntime
from planetmint_driver import Planetmint
#bdb_root_url = 'https://ipdb3.riddleandcode.com'

def test_zenroom_signing():
#    bdb_root_url = 'http://localhost:9984/'
#    bdb = Planetmint(bdb_root_url)
    # generate the keypairs/wallets for biolabs and the hospital
    # the pacemaker will only e represented by its public key address
    # derived from the attached RFID tag's EPC code
    from planetmint_driver.crypto import generate_keypair, CryptoKeypair

    biolabs, hospital = generate_keypair(), generate_keypair()
    # biolabs = CryptoKeypair(private_key='2KF5Qx4ksFWQ7j7DgTj1jYhQ6eoP38WoyFVMjTR5hDgK', public_key='2KF5Qx4ksFWQ7j7DgTj1jYhQ6eoP38WoyFVMjTR5hDgK')

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
    rfid_token = {
        'data': {
            'token_for': {
                'UCODE_DNA': {
                    'EPC_serial_number': 'E2003787C9AE8209161AF72F',
                    'amount_issued': 100,
                    'pegged_to'    : 'SFR',
                    #'pub_key'      : elements.public_key,
                }
            },
            #'description': 'Biolab\'s blockchain settlement system for pacemakers.',
        },
    }
    version = '2.0'
    script = """Scenario 'TakeoutCTL': "To provision, the pacemaker id#527663 the first time and store the output as keypair.keys"
    Given that I am known as 'identifier'
    When I create my new keypair
    Then print all data
    """
    script2 = """Scenario 'TakeoutCTL': "For settlement, the pacemaker id#527663 with keypair.keys activated locck 'did:r3c:MBs2h46THPD3ezJ7Giisq5MJbuWo7mpz8GF9NbW1BspjoICAgIGtleXJpbmcgPSBFQ0RILm5ldygpCiAgICBrZXlyaW5nOmtleWdlbigpCiAgICAKICAgIC0tIGV4cG9ydCB0aGUga2V5cGFpciB0byBqc29uCiAgICBleHBvcnQgPSBKU09OLmVuY29kZSgKICAgICAgIHsKICAgICAgICAgIHB1YmxpYyAgPSBrZXlyaW5nOiBwdWJsaWMoKTpiYXNlNjQoKSwKICAgICAgICAgIHByaXZhdGUgPSBrZXlyaW5nOnByaXZhdGUoKTpiYXNlNjQoKQogICAgICAgfQogICAgKQogICAgcHJpbnQoZXhwb3J0KQoWBE5vbmUWBE5vbmUWBE5vbmUCAQA='"
    Given that I am known as 'identifier'
    When my signature validated
    Then verify transaction and settle
    """
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


    # CRYPTO-CONDITIONS: instantiate an Ed25519|Zenroom crypto-condition for hospital
    #ed25519 = Ed25519Sha256(public_key=base58.b58decode(hospital.public_key))
    zenroomscpt = ZenroomSha256(script=script2, data=ZENROOM_DATA, keys=zen_public_keys)
    # print(F'ed25519 is: {ed25519.public_key}')
    print(F'zenroom is: {zenroomscpt.script}')
    # CRYPTO-CONDITIONS: generate the condition uri
    # condition_uri = ed25519.condition.serialize_uri()
    condition_uri_zen = zenroomscpt.condition.serialize_uri()
    #print(F'condition_uri is: {condition_uri}')
    # # print(F'condition_uri_zen is: {condition_uri_zen}')
    # ZEN-CRYPTO-CONDITION: generate the condition did
    zen_condition_did = 'did:bdb:MIIBMxaCARoKICAgIC0tIGdlbmVyYXRlIGEgc2ltcGxlIGtleXJpbmcKICAgIGtleXJpbmcgPSBFQ0RILm5ldygpCiAgICBrZXlyaW5nOmtleWdlbigpCiAgICAKICAgIC0tIGV4cG9ydCB0aGUga2V5cGFpciB0byBqc29uCiAgICBleHBvcnQgPSBKU09OLmVuY29kZSgKICAgICAgIHsKICAgICAgICAgIHB1YmxpYyAgPSBrZXlyaW5nOiBwdWJsaWMoKTpiYXNlNjQoKSwKICAgICAgICAgIHByaXZhdGUgPSBrZXlyaW5nOnByaXZhdGUoKTpiYXNlNjQoKQogICAgICAgfQogICAgKQogICAgcHJpbnQoZXhwb3J0KQoWBE5vbmUWBE5vbmUWBE5vbmUCAQA='
    # CRYPTO-CONDITIONS: construct an unsigned fulfillment dictionary
    """unsigned_fulfillment_dict = {
        'type': ed25519.TYPE_NAME,
        'public_key': base58.b58encode(ed25519.public_key).decode(),
    }"""
    unsigned_fulfillment_dict_zen = {
        'type': zenroomscpt.TYPE_NAME,
        'public_key': base58.b58encode(hospital.public_key).decode(),
    }
    output = {
        'amount': '10',
        'condition': {
            #'details': unsigned_fulfillment_dict,
            'details': unsigned_fulfillment_dict_zen,
            #'uri': condition_uri,
            'uri': condition_uri_zen,
            #'did': zen_condition_did,
            #'script': script,
            #'keys': '',
            #'data': '',
            #'conf': '',zenroomscpt
            #'verbosity': '0',
        },
        'public_keys': [hospital.public_key,],
    }
    input_ = {
        'fulfillment': None,
        'fulfills': None,
        'owners_before': [biolabs.public_key,]
    }
    token_creation_tx = {
        'operation': 'CREATE',
        'asset': rfid_token,
        'metadata': None,
        'outputs': (output,),
        'inputs': (input_,),
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
    message = sha3.sha3_256(message.encode())
    # CRYPTO-CONDITIONS: sign the serialized transaction-without-id
    #ed25519.sign(message.digest(), base58.b58decode(biolabs.private_key))
    ##  zenroomscpt.sign(message.digest(), base58.b58decode(biolabs.private_key))
    # CRYPTO-CONDITIONS: check the zenroom script
    #ed25519.zenroom = script
    # CRYPTO-CONDITIONS: generate the fulfillment uri
    # fulfillment_uri = ed25519.serialize_uri()
    fulfillment_uri_zen = zenroomscpt.serialize_uri()
    print(f'\nfulfillment_uri_zen is: {fulfillment_uri_zen}\n\n')
    fulfillment_fromuri_zen = zenroomscpt.from_uri(fulfillment_uri_zen)
    # print(F'fulfillment_uri is: {fulfillment_uri}')

    print(f'\nfulfillment_fromuri_zen is: {fulfillment_fromuri_zen}\n\n')
    print(f"\nfulfillment from uri dict: {fulfillment_fromuri_zen.__dict__}\n")
    print(f"\nkey : {hospital.public_key}\n")
    print(f"\nfulfillment from uri zenscript :  {fulfillment_fromuri_zen.script}\n")
    print()
    ## print(fulfillment_fromuri_zen.signature.hex())
    print('\n')
    ## print(fulfillment_frofulfillment_uri_zenmuri_zen.validate(message=message.digest()))
    #vk = VerifyKey(fulfillment_fromuri_zen.public_key)
    #vk.verify(fulfillment_fromuri_zen.signature, message.digest())
    #  pGSAIP5dZUoZ4y219VVzwHUVFWavq9ZiKeUb7CTyWzqGQE6ZgUDK9QIdbA7GjVSq6Mg7i3d6Cp22MyeRkpBY3oqhBz4owCQ7L6YtO9D2CrxPnMpdxdF2McdfL0QxR6gIycZnUPcO
    #  pWSAIP5dZUoZ4y219VVzwHUVFWavq9ZiKeUb7CTyWzqGQE6ZgUDK9QIdbA7GjVSq6Mg7i3d6Cp22MyeRkpBY3oqhBz4owCQ7L6YtO9D2CrxPnMpdxdF2McdfL0QxR6gIycZnUPcO
    # add the fulfillment uri (signature)
    token_creation_tx['inputs'][0]['fulfillment'] = fulfillment_uri_zen ## there is the problem with fulfillment uri
    #token_creation_tx['inputs'][0]['fulfillment'] = fulfillment_uri ## there is the problem with fulfillment uri
    #print(F'token_creation_tx is: {token_creation_tx}')
    # JSON: serialize the id-less transaction to a json formatted string
    json_str_tx = json.dumps(
        token_creation_tx,
        sort_keys=True,
        separators=(',', ':'),
        ensure_ascii=False,
    )
    # SHA3: hash the serialized id-less transaction to generate the id
    shared_creation_txid = sha3.sha3_256(json_str_tx.encode()).hexdigest()
    # add the id
    token_creation_tx['id'] = shared_creation_txid
    print(F'The TX to be consensed: {token_creation_tx}')
    # send CREATE tx into the bdb network

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
    
    #assert status_code == 202
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    #returned_creation_tx = bdb.transactions.send_async(token_creation_tx)
    #print(f"created TX : {returned_creation_tx}" )
    # result, errors = zenroom.zencode_exec(script)
    # result, errors = zenroom.zencode_exec(script)
    #print(result)
    '''
    Settlement on the Magic Mote chain is a prerequisite to sttlement on the respective settlement chain,
    Liquid, Ethereum, Bitcoin, Hyperledger Fabric or Coreda R3.
    Therefore, policies can become part of the transaction fulfillment logic. Quite exciting.
    This way the Oracle Servce ith built right inro the transaction itself.
    More precisely, it is part of the fulfillment.
    Therefore, interweaving the blockchain transactions with external systems becomes trivial.
    Add to this the capability to multipart each and every transaction thanks to code mobility
    and thanks to transferring code with the state of the VM itself, the power of the system
    becomes comprehensible.
    Then consider that each and evry transaction is enabled to carry around its very own
    interface to visualize transaction and chainstate on DLT enabled machines via the
    Magic Mote UI.
    Smart dust , indeed.
    '''
