import base64
import binascii
import codecs

from tendermint.abci import types_pb2
from tendermint.crypto import keys_pb2
from planetmint.transactions.common.exceptions import InvalidPublicKey


def encode_validator(v):
    ed25519_public_key = v['public_key']['value']
    pub_key = keys_pb2.PublicKey(ed25519=bytes.fromhex(ed25519_public_key))

    return types_pb2.ValidatorUpdate(pub_key=pub_key, power=v['power'])


def decode_validator(v):
    return {'public_key': {'type': 'ed25519-base64',
                           'value': codecs.encode(v.pub_key.ed25519, 'base64').decode().rstrip('\n')},
            'voting_power': v.power}


def new_validator_set(validators, updates):
    validators_dict = {}
    for v in validators:
        validators_dict[v['public_key']['value']] = v

    updates_dict = {}
    for u in updates:
        decoder = get_public_key_decoder(u['public_key'])
        public_key64 = base64.b64encode(decoder(u['public_key']['value'])).decode('utf-8')
        updates_dict[public_key64] = {'public_key': {'type': 'ed25519-base64',
                                                     'value': public_key64},
                                      'voting_power': u['power']}

    new_validators_dict = {**validators_dict, **updates_dict}
    return list(new_validators_dict.values())


def encode_pk_to_base16(validator):
    pk = validator['public_key']
    decoder = get_public_key_decoder(pk)
    public_key16 = base64.b16encode(decoder(pk['value'])).decode('utf-8')

    validator['public_key']['value'] = public_key16
    return validator


def validate_asset_public_key(pk):
    pk_binary = pk['value'].encode('utf-8')
    decoder = get_public_key_decoder(pk)
    try:
        pk_decoded = decoder(pk_binary)
        if len(pk_decoded) != 32:
            raise InvalidPublicKey('Public key should be of size 32 bytes')

    except binascii.Error:
        raise InvalidPublicKey('Invalid `type` specified for public key `value`')


def get_public_key_decoder(pk):
    encoding = pk['type']
    decoder = base64.b64decode

    if encoding == 'ed25519-base16':
        decoder = base64.b16decode
    elif encoding == 'ed25519-base32':
        decoder = base64.b32decode
    elif encoding == 'ed25519-base64':
        decoder = base64.b64decode
    else:
        raise InvalidPublicKey('Invalid `type` specified for public key `value`')

    return decoder
