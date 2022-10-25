# Copyright © 2020 Interplanetary Database Association e.V.,
# Planetmint and IPDB software contributors.
# SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
# Code is Apache-2.0 and docs are CC-BY-4.0

import base64
import hashlib
import json
import codecs

from binascii import hexlify
from tendermint.abci import types_pb2
from tendermint.crypto import keys_pb2
from hashlib import sha3_256
from transactions.common.exceptions import InvalidPublicKey


def encode_validator(v):
    ed25519_public_key = v["public_key"]["value"]
    pub_key = keys_pb2.PublicKey(ed25519=bytes.fromhex(ed25519_public_key))

    return types_pb2.ValidatorUpdate(pub_key=pub_key, power=v["power"])


def decode_validator(v):
    return {
        "public_key": {
            "type": "ed25519-base64",
            "value": codecs.encode(v.pub_key.ed25519, "base64").decode().rstrip("\n"),
        },
        "voting_power": v.power,
    }


def new_validator_set(validators, updates):
    validators_dict = {}
    for v in validators:
        validators_dict[v["public_key"]["value"]] = v

    updates_dict = {}
    for u in updates:
        decoder = get_public_key_decoder(u["public_key"])
        public_key64 = base64.b64encode(decoder(u["public_key"]["value"])).decode("utf-8")
        updates_dict[public_key64] = {
            "public_key": {"type": "ed25519-base64", "value": public_key64},
            "voting_power": u["power"],
        }

    new_validators_dict = {**validators_dict, **updates_dict}
    return list(new_validators_dict.values())


def get_public_key_decoder(pk):
    encoding = pk["type"]
    decoder = base64.b64decode

    if encoding == "ed25519-base16":
        decoder = base64.b16decode
    elif encoding == "ed25519-base32":
        decoder = base64.b32decode
    elif encoding == "ed25519-base64":
        decoder = base64.b64decode
    else:
        raise InvalidPublicKey("Invalid `type` specified for public key `value`")

    return decoder


def encode_transaction(value):
    """Encode a transaction (dict) to Base64."""

    return base64.b64encode(json.dumps(value).encode("utf8")).decode("utf8")


def decode_transaction(raw):
    """Decode a transaction from bytes to a dict."""

    return json.loads(raw.decode("utf8"))


def decode_transaction_base64(value):
    """Decode a transaction from Base64."""

    return json.loads(base64.b64decode(value.encode("utf8")).decode("utf8"))


def calculate_hash(key_list):
    if not key_list:
        return ""

    full_hash = sha3_256()
    for key in key_list:
        full_hash.update(key.encode("utf8"))

    return full_hash.hexdigest()


def merkleroot(hashes):
    """Computes the merkle root for a given list.

    Args:
        hashes (:obj:`list` of :obj:`bytes`): The leaves of the tree.

    Returns:
        str: Merkle root in hexadecimal form.

    """
    # XXX TEMPORARY -- MUST REVIEW and possibly CHANGE
    # The idea here is that the UTXO SET would be empty and this function
    # would be invoked to compute the merkle root, and since there is nothing,
    # i.e. an empty list, then the hash of the empty string is returned.
    # This seems too easy but maybe that is good enough? TO REVIEW!
    if not hashes:
        return sha3_256(b"").hexdigest()
    # XXX END TEMPORARY -- MUST REVIEW ...
    if len(hashes) == 1:
        return hexlify(hashes[0]).decode()
    if len(hashes) % 2 == 1:
        hashes.append(hashes[-1])
    parent_hashes = [sha3_256(hashes[i] + hashes[i + 1]).digest() for i in range(0, len(hashes) - 1, 2)]
    return merkleroot(parent_hashes)


# ripemd160 is only available below python 3.9.13
@DeprecationWarning
def public_key64_to_address(base64_public_key):
    """Note this only compatible with Tendermint 0.19.x"""
    ed25519_public_key = public_key_from_base64(base64_public_key)
    encoded_public_key = amino_encoded_public_key(ed25519_public_key)
    return hashlib.new("ripemd160", encoded_public_key).hexdigest().upper()


def public_key_from_base64(base64_public_key):
    return key_from_base64(base64_public_key)


def key_from_base64(base64_key):
    return base64.b64decode(base64_key).hex().upper()


def public_key_to_base64(ed25519_public_key):
    return key_to_base64(ed25519_public_key)


def key_to_base64(ed25519_key):
    ed25519_key = bytes.fromhex(ed25519_key)
    return base64.b64encode(ed25519_key).decode("utf-8")


def amino_encoded_public_key(ed25519_public_key):
    return bytes.fromhex("1624DE6220{}".format(ed25519_public_key))
