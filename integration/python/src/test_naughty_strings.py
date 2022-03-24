# Copyright © 2020 Interplanetary Database Association e.V.,
# Planetmint and IPDB software contributors.
# SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
# Code is Apache-2.0 and docs are CC-BY-4.0

# ## Testing potentially hazardous strings
# This test uses a library of `naughty` strings (code injections, weird unicode chars., etc.) as both keys and values.
# We look for either a successful tx, or in the case that we use a naughty string as a key, and it violates some key
# constraints, we expect to receive a well formatted error message.

# ## Imports
# Since the naughty strings get encoded and decoded in odd ways,
# we'll use a regex to sweep those details under the rug.
import re

# We'll use a nice library of naughty strings...
from blns import blns

# And parameterize our test so each one is treated as a separate test case
import pytest

# For this test case we import and use the Python Driver.
from planetmint_driver.crypto import generate_keypair
from planetmint_driver.exceptions import BadRequest

# import helper to manage multiple nodes
from .helper.hosts import Hosts

naughty_strings = blns.all()


# This is our base test case, but we'll reuse it to send naughty strings as both keys and values.
def send_naughty_tx(asset, metadata):
    # ## Set up a connection to Planetmint
    # Check [test_basic.py](./test_basic.html) to get some more details
    # about the endpoint.
    hosts = Hosts('/shared/hostnames')
    pm = hosts.get_connection()

    # Here's Alice.
    alice = generate_keypair()

    # Alice is in a naughty mood today, so she creates a tx with some naughty strings
    prepared_transaction = pm.transactions.prepare(
        operation='CREATE',
        signers=alice.public_key,
        asset=asset,
        metadata=metadata)

    # She fulfills the transaction
    fulfilled_transaction = pm.transactions.fulfill(
        prepared_transaction,
        private_keys=alice.private_key)

    # The fulfilled tx gets sent to the pm network
    try:
        sent_transaction = pm.transactions.send_commit(fulfilled_transaction)
    except BadRequest as e:
        sent_transaction = e

    # If her key contained a '.', began with a '$', or contained a NUL character
    regex = r'.*\..*|\$.*|.*\x00.*'
    key = next(iter(metadata))
    if re.match(regex, key):
        # Then she expects a nicely formatted error code
        status_code = sent_transaction.status_code
        error = sent_transaction.error
        regex = (
            r'\{\s*\n*'
            r'\s*"message":\s*"Invalid transaction \(ValidationError\):\s*'
            r'Invalid key name.*The key name cannot contain characters.*\n*'
            r'\s*"status":\s*400\n*'
            r'\s*\}\n*')
        assert status_code == 400
        assert re.fullmatch(regex, error), sent_transaction
    # Otherwise, she expects to see her transaction in the database
    elif 'id' in sent_transaction.keys():
        tx_id = sent_transaction['id']
        assert pm.transactions.retrieve(tx_id)
    # If neither condition was true, then something weird happened...
    else:
        raise TypeError(sent_transaction)


@pytest.mark.parametrize("naughty_string", naughty_strings, ids=naughty_strings)
def test_naughty_keys(naughty_string):

    asset = {'data': {naughty_string: 'nice_value'}}
    metadata = {naughty_string: 'nice_value'}

    send_naughty_tx(asset, metadata)


@pytest.mark.parametrize("naughty_string", naughty_strings, ids=naughty_strings)
def test_naughty_values(naughty_string):

    asset = {'data': {'nice_key': naughty_string}}
    metadata = {'nice_key': naughty_string}

    send_naughty_tx(asset, metadata)
