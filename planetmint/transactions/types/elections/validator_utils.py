# Copyright © 2020 Interplanetary Database Association e.V.,
# Planetmint and IPDB software contributors.
# SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
# Code is Apache-2.0 and docs are CC-BY-4.0

import base58
import base64
import binascii

from planetmint.transactions.common.exceptions import InvalidPublicKey


def encode_pk_to_base16(validator):
    pk = validator["public_key"]
    decoder = get_public_key_decoder(pk)
    public_key16 = base64.b16encode(decoder(pk["value"])).decode("utf-8")

    validator["public_key"]["value"] = public_key16
    return validator


def validate_asset_public_key(pk):
    pk_binary = pk["value"].encode("utf-8")
    decoder = get_public_key_decoder(pk)
    try:
        pk_decoded = decoder(pk_binary)
        if len(pk_decoded) != 32:
            raise InvalidPublicKey("Public key should be of size 32 bytes")

    except binascii.Error:
        raise InvalidPublicKey("Invalid `type` specified for public key `value`")


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


def election_id_to_public_key(election_id):
    return base58.b58encode(bytes.fromhex(election_id)).decode()
