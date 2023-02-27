# Copyright © 2020 Interplanetary Database Association e.V.,
# Planetmint and IPDB software contributors.
# SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
# Code is Apache-2.0 and docs are CC-BY-4.0
from hashlib import sha3_256

import base58
import base64
import random

from functools import singledispatch

from planetmint import backend
from planetmint.abci.rpc import ABCI_RPC
from planetmint.backend.localmongodb.connection import LocalMongoDBConnection
from planetmint.backend.tarantool.connection import TarantoolDBConnection
from planetmint.backend.schema import TABLES
from transactions.common import crypto
from transactions.common.transaction_mode_types import BROADCAST_TX_COMMIT
from transactions.types.assets.create import Create
from transactions.types.elections.vote import Vote
from transactions.types.elections.validator_utils import election_id_to_public_key
from planetmint.abci.tendermint_utils import key_to_base64, merkleroot
from planetmint.abci.rpc import MODE_COMMIT, MODE_LIST


@singledispatch
def flush_db(connection, dbname):
    raise NotImplementedError


@flush_db.register(LocalMongoDBConnection)
def flush_localmongo_db(connection, dbname):
    for t in TABLES:
        getattr(connection.conn[dbname], t).delete_many({})


@flush_db.register(TarantoolDBConnection)
def flush_tarantool_db(connection, dbname):
    connection.connect().call("drop")
    connection.connect().call("init")


def generate_block(planet, test_abci_rpc):
    from transactions.common.crypto import generate_key_pair

    alice = generate_key_pair()
    tx = Create.generate([alice.public_key], [([alice.public_key], 1)], assets=[{"data": None}]).sign(
        [alice.private_key]
    )

    code, message = test_abci_rpc.write_transaction(
        MODE_LIST, test_abci_rpc.tendermint_rpc_endpoint, MODE_COMMIT, tx, BROADCAST_TX_COMMIT
    )
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


def delete_unspent_outputs(connection, *unspent_outputs):
    """Deletes the given ``unspent_outputs`` (utxos).

    Args:
        *unspent_outputs (:obj:`tuple` of :obj:`dict`): Variable
            length tuple or list of unspent outputs.
    """
    if unspent_outputs:
        return backend.query.delete_unspent_outputs(connection, *unspent_outputs)


def get_utxoset_merkle_root(connection):
    """Returns the merkle root of the utxoset. This implies that
    the utxoset is first put into a merkle tree.

    For now, the merkle tree and its root will be computed each
    time. This obviously is not efficient and a better approach
    that limits the repetition of the same computation when
    unnecesary should be sought. For instance, future optimizations
    could simply re-compute the branches of the tree that were
    affected by a change.

    The transaction hash (id) and output index should be sufficient
    to uniquely identify a utxo, and consequently only that
    information from a utxo record is needed to compute the merkle
    root. Hence, each node of the merkle tree should contain the
    tuple (txid, output_index).

    .. important:: The leaves of the tree will need to be sorted in
        some kind of lexicographical order.

    Returns:
        str: Merkle root in hexadecimal form.
    """
    utxoset = backend.query.get_unspent_outputs(connection)
    # TODO Once ready, use the already pre-computed utxo_hash field.
    # See common/transactions.py for details.
    hashes = [
        sha3_256("{}{}".format(utxo["transaction_id"], utxo["output_index"]).encode()).digest() for utxo in utxoset
    ]
    # TODO Notice the sorted call!
    return merkleroot(sorted(hashes))


def store_unspent_outputs(connection, *unspent_outputs):
    """Store the given ``unspent_outputs`` (utxos).

    Args:
        *unspent_outputs (:obj:`tuple` of :obj:`dict`): Variable
            length tuple or list of unspent outputs.
    """
    if unspent_outputs:
        return backend.query.store_unspent_outputs(connection, *unspent_outputs)


def update_utxoset(connection, transaction):
    """
    Update the UTXO set given ``transaction``. That is, remove
    the outputs that the given ``transaction`` spends, and add the
    outputs that the given ``transaction`` creates.

    Args:
        transaction (:obj:`~planetmint.models.Transaction`): A new
            transaction incoming into the system for which the UTXOF
            set needs to be updated.
    """
    spent_outputs = [spent_output for spent_output in transaction.spent_outputs]
    if spent_outputs:
        delete_unspent_outputs(connection, *spent_outputs)
    store_unspent_outputs(connection, *[utxo._asdict() for utxo in transaction.unspent_outputs])