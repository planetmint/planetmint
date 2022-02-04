# Copyright © 2020 Interplanetary Database Association e.V.,
# Planetmint and IPDB software contributors.
# SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
# Code is Apache-2.0 and docs are CC-BY-4.0

import pytest
import codecs

from tendermint.abci import types_pb2 as types
from tendermint.crypto import keys_pb2

@pytest.fixture
def validator_pub_key():
    return 'B0E42D2589A455EAD339A035D6CE1C8C3E25863F268120AA0162AD7D003A4014'


@pytest.fixture
def init_chain_request():
    pk = codecs.decode(b'VAgFZtYw8bNR5TMZHFOBDWk9cAmEu3/c6JgRBmddbbI=',
                       'base64')
    val_a = types.ValidatorUpdate(power=10,
                                  pub_key=keys_pb2.PublicKey(ed25519=pk))
    return types.RequestInitChain(validators=[val_a])
