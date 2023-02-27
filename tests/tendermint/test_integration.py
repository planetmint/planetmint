# Copyright © 2020 Interplanetary Database Association e.V.,
# Planetmint and IPDB software contributors.
# SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
# Code is Apache-2.0 and docs are CC-BY-4.0

import codecs
import json
import pytest

from transactions.types.assets.create import Create
from transactions.types.assets.transfer import Transfer
from tendermint.abci import types_pb2 as types
from abci.server import ProtocolHandler
from abci.utils import read_messages
from transactions.common.transaction_mode_types import BROADCAST_TX_COMMIT, BROADCAST_TX_SYNC

from planetmint.abci.rpc import MODE_COMMIT, MODE_LIST
from planetmint.version import __tm_supported_versions__
from io import BytesIO


@pytest.mark.bdb
def test_app(b, eventqueue_fixture, init_chain_request):
    from planetmint.abci.application_logic import ApplicationLogic
    from planetmint.abci.utils import calculate_hash
    from transactions.common.crypto import generate_key_pair

    app = ApplicationLogic(b, eventqueue_fixture)
    p = ProtocolHandler(app)

    data = p.process("info", types.Request(info=types.RequestInfo(version=__tm_supported_versions__[0])))
    res = next(read_messages(BytesIO(data), types.Response))
    assert res
    assert res.info.last_block_app_hash == b""
    assert res.info.last_block_height == 0
    assert not b.models.get_latest_block()

    p.process("init_chain", types.Request(init_chain=init_chain_request))
    block0 = b.models.get_latest_block()
    assert block0
    assert block0["height"] == 0
    assert block0["app_hash"] == ""

    pk = codecs.encode(init_chain_request.validators[0].pub_key.ed25519, "base64").decode().strip("\n")
    [validator] = b.models.get_validators(height=1)
    assert validator["public_key"]["value"] == pk
    assert validator["voting_power"] == 10

    alice = generate_key_pair()
    bob = generate_key_pair()
    tx = Create.generate([alice.public_key], [([bob.public_key], 1)]).sign([alice.private_key])
    etxn = json.dumps(tx.to_dict()).encode("utf8")

    r = types.Request(check_tx=types.RequestCheckTx(tx=etxn))
    data = p.process("check_tx", r)
    res = next(read_messages(BytesIO(data), types.Response))
    assert res
    assert res.check_tx.code == 0

    r = types.Request()
    r.begin_block.hash = b""
    p.process("begin_block", r)

    r = types.Request(deliver_tx=types.RequestDeliverTx(tx=etxn))
    data = p.process("deliver_tx", r)
    res = next(read_messages(BytesIO(data), types.Response))
    assert res
    assert res.deliver_tx.code == 0

    new_block_txn_hash = calculate_hash([tx.id])

    r = types.Request(end_block=types.RequestEndBlock(height=1))
    data = p.process("end_block", r)
    res = next(read_messages(BytesIO(data), types.Response))
    assert res
    assert "end_block" == res.WhichOneof("value")

    new_block_hash = calculate_hash([block0["app_hash"], new_block_txn_hash])

    data = p.process("commit", None)
    res = next(read_messages(BytesIO(data), types.Response))
    assert res.commit.data == new_block_hash.encode("utf-8")
    assert b.models.get_transaction(tx.id).id == tx.id

    block0 = b.models.get_latest_block()
    assert block0
    assert block0["height"] == 1
    assert block0["app_hash"] == new_block_hash

    # empty block should not update height
    r = types.Request()
    r.begin_block.hash = new_block_hash.encode("utf-8")
    p.process("begin_block", r)

    r = types.Request()
    r.end_block.height = 2
    p.process("end_block", r)

    data = p.process("commit", None)
    res = next(read_messages(BytesIO(data), types.Response))
    assert res.commit.data == new_block_hash.encode("utf-8")

    block0 = b.models.get_latest_block()
    assert block0
    assert block0["height"] == 2

    # when empty block is generated hash of previous block should be returned
    assert block0["app_hash"] == new_block_hash


@pytest.mark.abci
def test_post_transaction_responses(tendermint_ws_url, b, test_abci_rpc):
    from transactions.common.crypto import generate_key_pair

    alice = generate_key_pair()
    bob = generate_key_pair()
    tx = Create.generate(
        [alice.public_key],
        [([alice.public_key], 1)],
        assets=[{"data": "QmaozNR7DZHQK1ZcU9p7QdrshMvXqWK6gpu5rmrkPdT3L4"}],
    ).sign([alice.private_key])

    code, message = test_abci_rpc.write_transaction(
        MODE_LIST, test_abci_rpc.tendermint_rpc_endpoint, MODE_COMMIT, tx, BROADCAST_TX_COMMIT
    )
    assert code == 202

    tx_transfer = Transfer.generate(tx.to_inputs(), [([bob.public_key], 1)], asset_ids=[tx.id]).sign(
        [alice.private_key]
    )

    code, message = test_abci_rpc.write_transaction(
        MODE_LIST, test_abci_rpc.tendermint_rpc_endpoint, MODE_COMMIT, tx_transfer, BROADCAST_TX_COMMIT
    )
    assert code == 202

    carly = generate_key_pair()
    double_spend = Transfer.generate(
        tx.to_inputs(),
        [([carly.public_key], 1)],
        asset_ids=[tx.id],
    ).sign([alice.private_key])
    for mode in (BROADCAST_TX_SYNC, BROADCAST_TX_COMMIT):
        code, message = test_abci_rpc.write_transaction(
            MODE_LIST, test_abci_rpc.tendermint_rpc_endpoint, MODE_COMMIT, double_spend, mode
        )
        assert code == 500
        assert message == "Transaction validation failed"
