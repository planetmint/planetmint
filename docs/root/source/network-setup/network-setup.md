<!---
Copyright © 2020 Interplanetary Database Association e.V.,
Planetmint and IPDB software contributors.
SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
Code is Apache-2.0 and docs are CC-BY-4.0
--->

# How to Set Up a Planetmint Network

You can setup or connect to a network once you have a single node running.
Until now, everything could be done by a node operator, by themselves.
Now the node operators, also called **Members**, must share some information
with each other, so they can form a network.

There is one special Member who helps coordinate everyone: the **Coordinator**.

## Member: Share hostname, pub_key.value and node_id

Each Planetmint node is identified by its:

* `hostname`, i.e. the node's DNS subdomain, such as `bnode.example.com`, or its IP address, such as `46.145.17.32`
* Tendermint `pub_key.value`
* Tendermint `node_id`

The Tendermint `pub_key.value` is stored
in the file `$HOME/.tendermint/config/priv_validator.json`.
That file should look like:

```json
{
  "address": "E22D4340E5A92E4A9AD7C62DA62888929B3921E9",
  "pub_key": {
    "type": "tendermint/PubKeyEd25519",
    "value": "P+aweH73Hii8RyCmNWbwPsa9o4inq3I+0fSfprVkZa0="
  },
  "last_height": "0",
  "last_round": "0",
  "last_step": 0,
  "priv_key": {
    "type": "tendermint/PrivKeyEd25519",
    "value": "AHBiZXdZhkVZoPUAiMzClxhl0VvUp7Xl3YT6GvCc93A/5rB4fvceKLxHIKY1ZvA+xr2jiKercj7R9J+mtWRlrQ=="
  }
}
```

To get your Tendermint `node_id`, run the command:

```
tendermint show_node_id
```

An example `node_id` is `9b989cd5ac65fec52652a457aed6f5fd200edc22`.

**Share your `hostname`, `pub_key.value` and `node_id` with all other Members.**

## Coordinator: Create & Share the genesis.json File

At this point the Coordinator should have received the data
from all the Members, and should combine them in the file
`$HOME/.tendermint/config/genesis.json`:

```json
{
   "genesis_time":"0001-01-01T00:00:00Z",
   "chain_id":"test-chain-la6HSr",
   "consensus_params":{
      "block_size_params":{
         "max_bytes":"22020096",
         "max_txs":"10000",
         "max_gas":"-1"
      },
      "tx_size_params":{
         "max_bytes":"10240",
         "max_gas":"-1"
      },
      "block_gossip_params":{
         "block_part_size_bytes":"65536"
      },
      "evidence_params":{
         "max_age":"100000"
      }
   },
   "validators":[
      {
         "pub_key":{
            "type":"tendermint/PubKeyEd25519",
            "value":"<Member 1 public key>"
         },
         "power":10,
         "name":"<Member 1 name>"
      },
      {
         "pub_key":{
            "type":"tendermint/PubKeyEd25519",
            "value":"<Member 2 public key>"
         },
         "power":10,
         "name":"<Member 2 name>"
      },
      {
         "...":{

         },

      },
      {
         "pub_key":{
            "type":"tendermint/PubKeyEd25519",
            "value":"<Member N public key>"
         },
         "power":10,
         "name":"<Member N name>"
      }
   ],
   "app_hash":""
}
```

**Note:** The above `consensus_params` in the `genesis.json`
are default values.

The new `genesis.json` file contains the data that describes the Network.
The key `name` is the Member's moniker; it can be any valid string,
but put something human-readable like `"Alice's Node Shop"`.

At this point, the Coordinator must share the new `genesis.json` file with all Members.

## Member: Connect to the Other Members

At this point the Member should have received the `genesis.json` file.

The Member must copy the `genesis.json` file
into their local `$HOME/.tendermint/config` directory.
Every Member now shares the same `chain_id` and `genesis_time` (used to identify the Network),
and the same list of `validators`.

Each Member must edit their `$HOME/.tendermint/config/config.toml` file
and make the following changes:

```
moniker = "Name of our node"
create_empty_blocks = false
log_level = "main:info,state:info,*:error"

persistent_peers = "<Member 1 node id>@<Member 1 hostname>:26656,\
<Member 2 node id>@<Member 2 hostname>:26656,\
<Member N node id>@<Member N hostname>:26656,"

send_rate = 102400000
recv_rate = 102400000

recheck = false
```

Note: The list of `persistent_peers` doesn't have to include all nodes
in the network.

## Member: Start Tarantool

You install Tarantool as described [here](https://www.tarantool.io/ru/download/os-installation/ubuntu/).

You can start it using the command `tarantool`.To run it in the background (so it will continue running after you logout), you can have to create a listener `box.cfg{listen=3301}`.


## Member: Start Planetmint and Tendermint Using Monit

This section describes how to manage the Planetmint and Tendermint processes using [Monit][monit], a small open-source utility for managing and monitoring Unix processes. Planetmint and Tendermint are managed together, because if Planetmint is stopped (or crashes) and is restarted, *Tendermint won't try reconnecting to it*. (That's not a bug. It's just how Tendermint works.)

Install Monit:

```
sudo apt install monit
```

If you installed the `planetmint` Python package as above, you should have the `planetmint-monit-config` script in your `PATH` now. Run the script to build a configuration file for Monit:

```
planetmint-monit-config
```

Run Monit as a daemon, instructing it to wake up every second to check on processes:

```
monit -d 1
```

Monit will run the Planetmint and Tendermint processes and restart them when they crash. If the root `planetmint_` process crashes, Monit will also restart the Tendermint process.

You can check the status by running `monit status` or `monit summary`.

By default, it will collect program logs into the `~/.planetmint-monit/logs` folder.

To learn more about Monit, use `monit -h` (help) or read [the Monit documentation][monit-manual].

Check `planetmint-monit-config -h` if you want to arrange a different folder for logs or some of the Monit internal artifacts.

If you want to start and manage the Planetmint and Tendermint processes yourself, then look inside the file [planetmint/pkg/scripts/planetmint-monit-config](https://github.com/planetmint/planetmint/blob/master/pkg/scripts/planetmint-monit-config) to see how *it* starts Planetmint and Tendermint.

## How Others Can Access Your Node

If you followed the above instructions, then your node should be publicly-accessible with Planetmint Root URL `https://hostname` or `http://hostname:9984`. That is, anyone can interact with your node using the [Planetmint HTTP API](../connecting/http-client-server-api) exposed at that address. The most common way to do that is to use one of the [Planetmint Drivers](../connecting/drivers).

[bdb:software]: https://github.com/planetmint/planetmint/
[bdb:pypi]: https://pypi.org/project/Planetmint/#history
[tendermint:releases]: https://github.com/tendermint/tendermint/releases
[monit]: https://www.mmonit.com/monit
[monit-manual]: https://mmonit.com/monit/documentation/monit.html
