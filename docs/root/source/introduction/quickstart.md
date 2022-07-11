<!---
Copyright © 2020 Interplanetary Database Association e.V.,
Planetmint and IPDB software contributors.
SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
Code is Apache-2.0 and docs are CC-BY-4.0
--->



# Quickstart 
Planetmint is a metadata blockchain. This introduction gives an overview about how to attest data to Planetmint. First, simple transaction creation and sending is shown. Thereafter, an introdcution about how to set up a single node or a cluster is given. 



## The IPDB Testnet - sending transactions
The IPDB foundation hosts a testnet server that is reset every night at 4am UTC.

The following sequence shows a simple asset notarization / attestion on that testnet:
Create a file named notarize.py

```
from planetmint_driver import Planetmint
from planetmint_driver.crypto import generate_keypair

plntmnt = Planetmint('https://test.ipdb.io')
alice = generate_keypair()
tx = plntmnt.transactions.prepare(
    operation='CREATE',
    signers=alice.public_key,
    asset={'data': {'message': 'Blockchain all the things!'}})
signed_tx = plntmnt.transactions.fulfill(
    tx,
    private_keys=alice.private_key)
plntmnt.transactions.send_commit(signed_tx)
```

install dependencies and execute it

```
$ pip install planetmint-driver
$ python notarize.py
```
# Install Planetmint
## Local Node
Planemtint is a Tendermint applicatoin with an attached database.
A basic installation installs the database, Tendermint and therafter Planetmint.

Planetmint currently supports Tarantool and MongoDB database. The installation is as follows:
```
# Tarantool
$ curl -L https://tarantool.io/release/2/installer.sh | bash 
$ sudo apt-get -y install tarantool
```
*Caveat:* Tarantool versions before [2.4.2](https://www.tarantool.io/en/doc/latest/release/2.4.2/) automatically enable and start a demonstration instance that listens on port `3301` by default. Refer to the [Tarantool documentation](https://www.tarantool.io/en/doc/latest/getting_started/getting_started_db/#creating-db-locally) for more information.

```
# MongoDB
$ sudo apt install mongodb
```
Tendermint can be installed and started as follows
```
$ wget https://github.com/tendermint/tendermint/releases/download/v0.34.15/tendermint_0.34.15_linux_amd64.tar.gz
$ tar zxf tendermint_0.34.15_linux_amd64.tar.gz
$ ./tendermint init
$ ./tendermint node --proxy_app=tcp://localhost:26658
```
Planetmint installs and starts as described below
```
$ pip install planetmint
$ planetmint configure
$ planetmint start
```

## Cluster of nodes
Setting up a cluster of nodes comes down to set up a cluster of tendermint nodes as documented at [Tendermint](https://docs.tendermint.com/v0.35/introduction/quick-start.html#cluster-of-nodes). In addition to that, the database and Planetmint need to be installed on the servers as described above. 

## Setup Instructions for Various Cases

- Quickstart link below
- [Set up a local Planetmint node for development, experimenting and testing](../node-setup/index)
- [Set up and run a Planetmint network](../network-setup/index)

## Develop an App Test 

To develop an app that talks to a Planetmint network, you'll want a test network to test it against. You have a few options:

1. The IPDB Test Network (or "Testnet") is a free-to-use, publicly-available test network that you can test against. It is available at [IPDB testnet](https://test.ipdb.io/).
1. You could also run a Planetmint node on you local machine. One way is to use this node setup guide with a one-node "network" by using the all-in-one docker solution, or manual installation and configuration of the components. Another way is to use one of the deployment methods listed in the [network setup guide](../network-setup/index) or in the [the docs about contributing to Planetmint](../contributing/index).
