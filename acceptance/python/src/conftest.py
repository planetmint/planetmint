# Copyright © 2020 Interplanetary Database Association e.V.,
# Planetmint and IPDB software contributors.
# SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
# Code is Apache-2.0 and docs are CC-BY-4.0

import pytest

GENERATE_KEYPAIR = \
    """Rule input encoding base58
    Rule output encoding base58
    Scenario 'ecdh': Create the keypair
    Given that I am known as 'Pippo'
    When I create the ecdh key
    When I create the testnet key
    Then print data"""

# secret key to public key
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

FULFILL_SCRIPT = \
    """Rule input encoding base58
    Rule output encoding base58
    Scenario 'ecdh': Bob verifies the signature from Alice
    Given I have a 'ecdh public key' from 'Alice'
    Given that I have a 'string dictionary' named 'houses' inside 'asset'
    Given I have a 'signature' named 'data.signature' inside 'result'
    When I verify the 'houses' has a signature in 'data.signature' by 'Alice'
    Then print the string 'ok'"""

HOUSE_ASSETS = [
    {
        "data": {
            "houses": [
                {
                    "name": "Harry",
                    "team": "Gryffindor",
                },
                {
                    "name": "Draco",
                    "team": "Slytherin",
                }
            ],
        }
    }
]

ZENROOM_DATA = {
    'also': 'more data'
}

CONDITION_SCRIPT = """Rule input encoding base58
    Rule output encoding base58
    Scenario 'ecdh': create the signature of an object
    Given I have the 'keys'
    Given that I have a 'string dictionary' named 'houses' inside 'asset'
    When I create the signature of 'houses'
    When I rename the 'signature' to 'data.signature'
    Then print the 'data.signature'"""

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
    return HOUSE_ASSETS

@pytest.fixture
def zenroom_data():
    return ZENROOM_DATA