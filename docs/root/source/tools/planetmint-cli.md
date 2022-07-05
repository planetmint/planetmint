<!---
Copyright © 2020 Interplanetary Database Association e.V.,
Planetmint and IPDB software contributors.
SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
Code is Apache-2.0 and docs are CC-BY-4.0
--->

# Command Line Interface (CLI)

The command-line command to interact with Planetmint Server is `planetmint`.


## planetmint \-\-help

Show help for the `planetmint` command. `planetmint -h` does the same thing.


## planetmint \-\-version

Show the version number. `planetmint -v` does the same thing.


## planetmint configure

Generate a local configuration file (which can be used to set some or all [Planetmint node configuration settings](../node-setup/configuration)). It will ask you for the values of some configuration settings.
If you press Enter for a value, it will use the default value.

At this point, only one database backend is supported: `tarantool`.

If you use the `-c` command-line option, it will generate the file at the specified path:
```text
planetmint -c path/to/new_config.json configure tarantool
```

If you don't use the `-c` command-line option, the file will be written to `$HOME/.planetmint` (the default location where Planetmint looks for a config file, if one isn't specified).

If you use the `-y` command-line option, then there won't be any interactive prompts: it will use the default values for all the configuration settings.
```text
planetmint -y configure tarantool
```


## planetmint show-config

Show the values of the [Planetmint node configuration settings](../node-setup/configuration).


## planetmint init

Create a backend database (local tarantool), all database tables/collections,
various backend database indexes, and the genesis block.


## planetmint drop

Drop (erase) the backend database (the local tarantool database used by this node).
You will be prompted to make sure.
If you want to force-drop the database (i.e. skipping the yes/no prompt), then use `planetmint -y drop`


## planetmint start

Start Planetmint. It always begins by trying a `planetmint init` first. See the documentation for `planetmint init`.
The database initialization step is optional and can be skipped by passing the `--no-init` flag, i.e. `planetmint start --no-init`.

### Options

The log level for the console can be set via the option `--log-level` or its
abbreviation `-l`. Example:

```bash
$ planetmint --log-level INFO start
```

The allowed levels are `DEBUG`, `INFO`, `WARNING`, `ERROR`, and `CRITICAL`.
For an explanation regarding these levels please consult the
[Logging Levels](https://docs.python.org/3.9/library/logging.html#levels)
section of Python's documentation.

For a more fine-grained control over the logging configuration you can use the
configuration file as documented under
[Configuration Settings](../node-setup/configuration).


## planetmint election

Manage elections to govern the Planetmint network. The specifics of the election process are defined in [BEP-18](https://github.com/planetmint/BEPs/tree/master/18).

Election management is broken into several subcommands. Below is the command line syntax for each of them.

### election new

Create a new election which proposes a change to the Planetmint network.

If the command succeeds, it will post an election transaction and output `election_id`.

The election proposal consists of vote tokens allocated to every current validator proportional to his voting power. Validators spend their votes to approve the election using the [election-approve command](election-approve).

Every election has a type. Currently supported types are `upsert-validator` and `chain-migration`. Their transaction operations are `VALIDATOR_ELECTION` and `CHAIN_MIGRATION` accordingly. See below for how to create an election of a particular type.

Note that elections can only be proposed and approved by existing validators.

#### election new upsert-validator

Create an election to add, update, or remove a validator.


```bash
$ planetmint election new upsert-validator <public-key> <power> <node-id> --private-key <path-to-the-private-key>
```

- `<public-key>` is the public key of the node to be added/updated/removed. The encoding and type of the key have to match those specified in `genesis.json` in the supported Tendermint version.
- `<power>` is the new power for the validator. To remove the validator, set the power to `0`.
- `<node-id>` is the node identifier from Tendermint. A node operator can learn his node identifier by executing `tendermint show_node_id`.
- `<path-to-the-private-key>` is the path to the private key of the validator who proposes the election. Tendermint places it at  `.tendermint/config/priv_validator.json`.

Example:

```bash
$ planetmint election new upsert-validator HHG0IQRybpT6nJMIWWFWhMczCLHt6xcm7eP52GnGuPY= 1 fb7140f03a4ffad899fabbbf655b97e0321add66 --private-key /home/user/.tendermint/config/priv_validator.json
[SUCCESS] Submitted proposal with id: 04a067582cf03eba2b53b82e4adb5ece424474cbd4f7183780855a93ac5e3caa
```

A successful execution of the above command does not imply the validator set has been updated but rather the proposal has been accepted by the network.
Once `election_id` has been generated, the proposer should share it with other validators of the network (e.g. via email) and ask them to approve the proposal.

Note that election proposers do not automatically approve elections by proposing them.

For more details about how validator set changes work, refer to [BEP-21](https://github.com/planetmint/BEPs/tree/master/21).

#### election new chain-migration

Create an election to halt block production, to coordinate on making a Tendermint upgrade with a backwards-incompatible chain.


```bash
$ planetmint election new chain-migration --private-key <path-to-the-private-key>
```

- `<path-to-the-private-key>` is the path to the private key of the validator who proposes the election. Tendermint places it at  `.tendermint/config/priv_validator.json`.


Example:

```bash
$ planetmint election new migration --private-key /home/user/.tendermint/config/priv_validator.json
[SUCCESS] Submitted proposal with id: 04a067582cf03eba2b53b82e4adb5ece424474cbd4f7183780855a93ac5e3caa
```

Concluded chain migration elections halt block production at whichever block height they are approved.
Afterwards, validators are supposed to upgrade Tendermint, set new `chain_id`, `app_hash`, and `validators` (to learn these values, use the [election show](#election-show) command) in `genesis.json`, make and save a tarantool dump, and restart the system.


For more details about how chain migrations work, refer to [Type 3 scenarios in BEP-42](https://github.com/planetmint/BEPs/tree/master/42).

(election-approve)=
### election approve

Approve an election by voting for it. The command places a `VOTE` transaction, spending all of the validator's vote tokens to the election address.


 ```bash
$ planetmint election approve <election-id> --private-key <path-to-the-private-key>
```

- `election-id` is the election identifier the approval is given for.
- `<path-to-the-private-key>` is the path to the private key of the validator who votes for the election. Tendermint places it at  `.tendermint/config/priv_validator.json`.

Example:
 ```bash
$ planetmint election approve 04a067582cf03eba2b53b82e4adb5ece424474cbd4f7183780855a93ac5e3caa --private-key /home/user/.tendermint/config/priv_validator.json
[SUCCESS] Your vote has been submitted
```

Once a proposal has been approved by the sufficient amount of validators (contributing more than `2/3` of the total voting power), the proposed change is applied to the network.

(election-show)=
### election show

Retrieves the information about elections.


```bash
$ planetmint election show <election-id>

status=<status>
```

`status` has three possible values:

- `ongoing`, if the election can be concluded but has not yet collected enough votes,
- `concluded`, if the election has been concluded,
- `inconclusive`, if the validator set changed while the election was in process, rendering it undecidable.

After a chain migration is concluded, the `show` command also outputs `chain_id`, `app_hash`, and `validators` for `genesis.json` of the new chain.

## planetmint tendermint-version

Show the Tendermint versions supported by Planetmint server.
```bash
$ planetmint tendermint-version
{
    "description": "Planetmint supports the following Tendermint version(s)",
    "tendermint": [
        "0.22.8"
    ]
}
```
