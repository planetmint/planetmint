# Copyright © 2020 Interplanetary Database Association e.V.,
# Planetmint and IPDB software contributors.
# SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
# Code is Apache-2.0 and docs are CC-BY-4.0

# ## Testing potentially hazardous strings
# This test uses a library of `naughty` strings (code injections, weird unicode chars., etc.) as both keys and values.
# We look for either a successful tx, or in the case that we use a naughty string as a key, and it violates some key
# constraints, we expect to receive a well formatted error message.

# ## Imports
# We need some utils from the `os` package, we will interact with
# env variables.
import os

# Since the naughty strings get encoded and decoded in odd ways,
# we'll use a regex to sweep those details under the rug.
import re
from tkinter import N
from unittest import skip

# We'll use a nice library of naughty strings...
from blns import blns

# And parameterize our test so each one is treated as a separate test case
import pytest

# For this test case we import and use the Python Driver.
from planetmint_driver import Planetmint
from planetmint_driver.crypto import generate_keypair
from planetmint_driver.exceptions import BadRequest
from ipld import multihash, marshal

naughty_strings = blns.all()
skipped_naughty_strings = [
    "1.00",
    "$1.00",
    "-1.00",
    "-$1.00",
    "0.00",
    "0..0",
    ".",
    "0.0.0",
    "-.",
    ",./;'[]\\-=",
    "ثم نفس سقطت وبالتحديد،, جزيرتي باستخدام أن دنو. إذ هنا؟ الستار وتنصيب كان. أهّل ايطاليا، بريطانيا-فرنسا قد أخذ. سليمان، إتفاقية بين ما, يذكر الحدود أي بعد, معاملة بولندا، الإطلاق عل إيو.",
    "test\x00",
    "Ṱ̺̺̕o͞ ̷i̲̬͇̪͙n̝̗͕v̟̜̘̦͟o̶̙̰̠kè͚̮̺̪̹̱̤ ̖t̝͕̳̣̻̪͞h̼͓̲̦̳̘̲e͇̣̰̦̬͎ ̢̼̻̱̘h͚͎͙̜̣̲ͅi̦̲̣̰̤v̻͍e̺̭̳̪̰-m̢iͅn̖̺̞̲̯̰d̵̼̟͙̩̼̘̳ ̞̥̱̳̭r̛̗̘e͙p͠r̼̞̻̭̗e̺̠̣͟s̘͇̳͍̝͉e͉̥̯̞̲͚̬͜ǹ̬͎͎̟̖͇̤t͍̬̤͓̼̭͘ͅi̪̱n͠g̴͉ ͏͉ͅc̬̟h͡a̫̻̯͘o̫̟̖͍̙̝͉s̗̦̲.̨̹͈̣",
    "̡͓̞ͅI̗̘̦͝n͇͇͙v̮̫ok̲̫̙͈i̖͙̭̹̠̞n̡̻̮̣̺g̲͈͙̭͙̬͎ ̰t͔̦h̞̲e̢̤ ͍̬̲͖f̴̘͕̣è͖ẹ̥̩l͖͔͚i͓͚̦͠n͖͍̗͓̳̮g͍ ̨o͚̪͡f̘̣̬ ̖̘͖̟͙̮c҉͔̫͖͓͇͖ͅh̵̤̣͚͔á̗̼͕ͅo̼̣̥s̱͈̺̖̦̻͢.̛̖̞̠̫̰",
    "̗̺͖̹̯͓Ṯ̤͍̥͇͈h̲́e͏͓̼̗̙̼̣͔ ͇̜̱̠͓͍ͅN͕͠e̗̱z̘̝̜̺͙p̤̺̹͍̯͚e̠̻̠͜r̨̤͍̺̖͔̖̖d̠̟̭̬̝͟i̦͖̩͓͔̤a̠̗̬͉̙n͚͜ ̻̞̰͚ͅh̵͉i̳̞v̢͇ḙ͎͟-҉̭̩̼͔m̤̭̫i͕͇̝̦n̗͙ḍ̟ ̯̲͕͞ǫ̟̯̰̲͙̻̝f ̪̰̰̗̖̭̘͘c̦͍̲̞͍̩̙ḥ͚a̮͎̟̙͜ơ̩̹͎s̤.̝̝ ҉Z̡̖̜͖̰̣͉̜a͖̰͙̬͡l̲̫̳͍̩g̡̟̼̱͚̞̬ͅo̗͜.̟",
    "̦H̬̤̗̤͝e͜ ̜̥̝̻͍̟́w̕h̖̯͓o̝͙̖͎̱̮ ҉̺̙̞̟͈W̷̼̭a̺̪͍į͈͕̭͙̯̜t̶̼̮s̘͙͖̕ ̠̫̠B̻͍͙͉̳ͅe̵h̵̬͇̫͙i̹͓̳̳̮͎̫̕n͟d̴̪̜̖ ̰͉̩͇͙̲͞ͅT͖̼͓̪͢h͏͓̮̻e̬̝̟ͅ ̤̹̝W͙̞̝͔͇͝ͅa͏͓͔̹̼̣l̴͔̰̤̟͔ḽ̫.͕",
    '"><script>alert(document.title)</script>',
    "'><script>alert(document.title)</script>",
    "><script>alert(document.title)</script>",
    "</script><script>alert(document.title)</script>",
    "< / script >< script >alert(document.title)< / script >",
    " onfocus=alert(document.title) autofocus ",
    '" onfocus=alert(document.title) autofocus ',
    "' onfocus=alert(document.title) autofocus ",
    "＜script＞alert(document.title)＜/script＞",
    "/dev/null; touch /tmp/blns.fail ; echo",
    "../../../../../../../../../../../etc/passwd%00",
    "../../../../../../../../../../../etc/hosts",
    "() { 0; }; touch /tmp/blns.shellshock1.fail;",
    "() { _; } >_[$($())] { touch /tmp/blns.shellshock2.fail; }",
]

naughty_strings = [naughty for naughty in naughty_strings if naughty not in skipped_naughty_strings]

# This is our base test case, but we'll reuse it to send naughty strings as both keys and values.
def send_naughty_tx(asset, metadata):
    # ## Set up a connection to Planetmint
    # Check [test_basic.py](./test_basic.html) to get some more details
    # about the endpoint.
    bdb = Planetmint(os.environ.get("PLANETMINT_ENDPOINT"))

    # Here's Alice.
    alice = generate_keypair()

    # Alice is in a naughty mood today, so she creates a tx with some naughty strings
    prepared_transaction = bdb.transactions.prepare(
        operation="CREATE", signers=alice.public_key, asset=asset, metadata=metadata
    )

    # She fulfills the transaction
    fulfilled_transaction = bdb.transactions.fulfill(prepared_transaction, private_keys=alice.private_key)

    # The fulfilled tx gets sent to the BDB network
    try:
        sent_transaction = bdb.transactions.send_commit(fulfilled_transaction)
    except BadRequest as e:
        sent_transaction = e

    # If her key contained a '.', began with a '$', or contained a NUL character
    regex = ".*\..*|\$.*|.*\x00.*"
    key = next(iter(metadata))
    if re.match(regex, key):
        # Then she expects a nicely formatted error code
        status_code = sent_transaction.status_code
        error = sent_transaction.error
        regex = (
            r"\{\s*\n*"
            r'\s*"message":\s*"Invalid transaction \(ValidationError\):\s*'
            r"Invalid key name.*The key name cannot contain characters.*\n*"
            r'\s*"status":\s*400\n*'
            r"\s*\}\n*"
        )
        assert status_code == 400
        assert re.fullmatch(regex, error), sent_transaction
    # Otherwise, she expects to see her transaction in the database
    elif "id" in sent_transaction.keys():
        tx_id = sent_transaction["id"]
        assert bdb.transactions.retrieve(tx_id)
    # If neither condition was true, then something weird happened...
    else:
        raise TypeError(sent_transaction)


@pytest.mark.parametrize("naughty_string", naughty_strings, ids=naughty_strings)
def test_naughty_keys(naughty_string):

    asset = {"data": multihash(marshal({naughty_string: "nice_value"}))}
    metadata = multihash(marshal({naughty_string: "nice_value"}))

    send_naughty_tx(asset, metadata)


@pytest.mark.parametrize("naughty_string", naughty_strings, ids=naughty_strings)
def test_naughty_values(naughty_string):

    asset = {"data": multihash(marshal({"nice_key": naughty_string}))}
    metadata = multihash(marshal({"nice_key": naughty_string}))

    send_naughty_tx(asset, metadata)
