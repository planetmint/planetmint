# Copyright © 2020 Interplanetary Database Association e.V.,
# Planetmint and IPDB software contributors.
# SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
# Code is Apache-2.0 and docs are CC-BY-4.0

import pytest

CONDITION_SCRIPT = """Scenario 'ecdh': create the signature of an object
    Given I have the 'keyring'
    Given that I have a 'string dictionary' named 'houses'
    When I create the signature of 'houses'
    Then print the 'signature'"""

FULFILL_SCRIPT = """Scenario 'ecdh': Bob verifies the signature from Alice
    Given I have a 'ecdh public key' from 'Alice'
    Given that I have a 'string dictionary' named 'houses'
    Given I have a 'signature' named 'signature'
    When I verify the 'houses' has a signature in 'signature' by 'Alice'
    Then print the string 'ok'"""

SK_TO_PK = """Scenario 'ecdh': Create the keypair
    Given that I am known as '{}'
    Given I have the 'keyring'
    When I create the ecdh public key
    When I create the bitcoin address
    Then print my 'ecdh public key'
    Then print my 'bitcoin address'"""

GENERATE_KEYPAIR = """Scenario 'ecdh': Create the keypair
    Given that I am known as 'Pippo'
    When I create the ecdh key
    When I create the bitcoin key
    Then print data"""

INITIAL_STATE = {"also": "more data"}
SCRIPT_INPUT = {
    "houses": [
        {
            "name": "Harry",
            "team": "Gryffindor",
        },
        {
            "name": "Draco",
            "team": "Slytherin",
        },
    ],
}

metadata = {"units": 300, "type": "KG"}

ZENROOM_DATA = {"that": "is my data"}


@pytest.fixture
def gen_key_zencode():
    return GENERATE_KEYPAIR


@pytest.fixture
def secret_key_to_private_key_zencode():
    return SK_TO_PK


@pytest.fixture
def fulfill_script_zencode():
    return FULFILL_SCRIPT


@pytest.fixture
def condition_script_zencode():
    return CONDITION_SCRIPT


@pytest.fixture
def zenroom_house_assets():
    return SCRIPT_INPUT


@pytest.fixture
def zenroom_script_input():
    return SCRIPT_INPUT


@pytest.fixture
def zenroom_data():
    return ZENROOM_DATA
