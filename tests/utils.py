# Copyright © 2020 Interplanetary Database Association e.V.,
# Planetmint and IPDB software contributors.
# SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
# Code is Apache-2.0 and docs are CC-BY-4.0

import base58
import base64
import random

from functools import singledispatch
from planetmint.backend.localmongodb.connection import LocalMongoDBConnection
from planetmint.backend.tarantool.connection import TarantoolDBConnection
from planetmint.backend.schema import TABLES, SPACE_NAMES
from transactions.common import crypto
from transactions.common.transaction_mode_types import BROADCAST_TX_COMMIT
from transactions.types.assets.create import Create
from transactions.types.elections.vote import Vote
from transactions.types.elections.validator_utils import election_id_to_public_key
from planetmint.tendermint_utils import key_to_base64


@singledispatch
def flush_db(connection, dbname):
    raise NotImplementedError


@flush_db.register(LocalMongoDBConnection)
def flush_localmongo_db(connection, dbname):
    for t in TABLES:
        getattr(connection.conn[dbname], t).delete_many({})


@flush_db.register(TarantoolDBConnection)
def flush_tarantool_db(connection, dbname):
    connection.connect().call('drop')
    connection.connect().call('init')


def generate_block(planet):
    from transactions.common.crypto import generate_key_pair

    alice = generate_key_pair()
    tx = Create.generate([alice.public_key], [([alice.public_key], 1)], assets=None).sign([alice.private_key])

    code, message = planet.write_transaction(tx, BROADCAST_TX_COMMIT)
    assert code == 202


def to_inputs(election, i, ed25519_node_keys):
    input0 = election.to_inputs()[i]
    votes = election.outputs[i].amount
    public_key0 = input0.owners_before[0]
    key0 = ed25519_node_keys[public_key0]
    return (input0, votes, key0)


def gen_vote(election, i, ed25519_node_keys):
    (input_i, votes_i, key_i) = to_inputs(election, i, ed25519_node_keys)
    election_pub_key = election_id_to_public_key(election.id)
    return Vote.generate([input_i], [([election_pub_key], votes_i)], election_ids=[election.id]).sign(
        [key_i.private_key]
    )


def generate_validators(powers):
    """Generates an arbitrary number of validators with random public keys.

    The object under the `storage` key is in the format expected by DB.

    The object under the `eleciton` key is in the format expected by
    the upsert validator election.

    `public_key`, `private_key` are in the format used for signing transactions.

    Args:
        powers: A list of intergers representing the voting power to
                assign to the corresponding validators.
    """
    validators = []
    for power in powers:
        kp = crypto.generate_key_pair()
        validators.append(
            {
                "storage": {
                    "public_key": {
                        "value": key_to_base64(base58.b58decode(kp.public_key).hex()),
                        "type": "ed25519-base64",
                    },
                    "voting_power": power,
                },
                "election": {
                    "node_id": f"node-{random.choice(range(100))}",
                    "power": power,
                    "public_key": {
                        "value": base64.b16encode(base58.b58decode(kp.public_key)).decode("utf-8"),
                        "type": "ed25519-base16",
                    },
                },
                "public_key": kp.public_key,
                "private_key": kp.private_key,
            }
        )
    return validators


# NOTE: This works for some but not for all test cases check if this or code base needs fix
def generate_election(b, cls, public_key, private_key, asset_data, voter_keys):
    voters = b.get_recipients_list()
    election = cls.generate([public_key], voters, asset_data, None).sign([private_key])

    votes = [
        Vote.generate([election.to_inputs()[i]], [([election_id_to_public_key(election.id)], power)], [election.id])
        for i, (_, power) in enumerate(voters)
    ]
    for key, v in zip(voter_keys, votes):
        v.sign([key])

    return election, votes
