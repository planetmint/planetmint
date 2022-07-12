<!---
Copyright © 2020 Interplanetary Database Association e.V.,
Planetmint and IPDB software contributors.
SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
Code is Apache-2.0 and docs are CC-BY-4.0
--->

# Migrate Bigchaindb cli for Tendermint

## Problem Description
With Tendermint integration some of the cli sub-commands have been rendered obsolete. It would be only appropriate to remove those sub-commands.

### Use cases
- Avoid confusing the user by not displaying irrelevant sub-commands.


## Proposed Change
Following sub-commands should be updated/removed:

- `planetmint --help`: list the relevant sub-commands for `localmongodb` backend.
`mongodb` and `rethinkdb` will be deprecated.
In case the backend is not configured then the default backend `localmongodb` should be assumed.

Following sub-commands should be deprecated for `localmongodb` backend.

- `planetmint export-my-pubkey`
  - A Planetmint node still has a public key but that is not Planetmint concern. It is handled by Tendermint.
- `planetmint set-shards`
  - This was only required for `rethinkdb`.
- `planetmint set-replicas`
  - This was only required for `rethinkdb`.
- `planetmint add-replicas`
  - This was only required for `mongodb` backend to add nodes to the MongoDB Replica Set, which is not required anymore,
    because we are using standalone MongoDB instances i.e. `localmongodb`.
- `planetmint remove-replicas`
  - This was only required for backend to remove nodes from the MongoDB Replica Set, which is not required anymore.

### Usage example
**planetmint**

```
$ planetmint --help
usage: planetmint [-h] [-c CONFIG] [-l {DEBUG,INFO,WARNING,ERROR,CRITICAL}]
                  [-y] [-v]
                  {configure,show-config,init,drop,start}
                  ...

Control your Planetmint node.

optional arguments:
  -h, --help            show this help message and exit
  -c CONFIG, --config CONFIG
                        Specify the location of the configuration file (use
                        "-" for stdout)
  -l {DEBUG,INFO,WARNING,ERROR,CRITICAL}, --log-level {DEBUG,INFO,WARNING,ERROR,CRITICAL}
                        Log level
  -y, --yes, --yes-please
                        Assume "yes" as answer to all prompts and run non-
                        interactively
  -v, --version         show program's version number and exit

Commands:
  {configure,show-config,export-my-pubkey,init,drop,start,set-shards,set-replicas,add-replicas,remove-replicas}
    configure           Prepare the config file
    show-config         Show the current configuration
    init                Init the database
    drop                Drop the database
    start               Start Planetmint
```

**planetmint configure**

```
$ planetmint configure --help
usage: planetmint configure [-h] {localmongodb}

positional arguments:
  {localmongodb}  The backend to use. It can be only be `localmongodb`.

optional arguments:
  -h, --help           show this help message and exit
```

**planetmint show-config**

```
$ planetmint show-config --help
usage: planetmint show-config [-h]

optional arguments:
  -h, --help  show this help message and exit
```

**planetmint init**

```
$ planetmint init --help
usage: planetmint init [-h]

optional arguments:
  -h, --help  show this help message and exit
```

**planetmint drop**

```
$ planetmint drop --help
usage: planetmint drop [-h]

optional arguments:
  -h, --help  show this help message and exit
```

**planetmint start**

```
$ planetmint start --help
usage: planetmint start [-h]
optional arguments:
  -h, --help            show this help message and exit
```

### Data model impact
N/A

### API impact
N/A

### Security impact
N/A

### Performance impact
N/A

### End user impact
N/A

### Deployment impact
N/A

### Documentation impact
Document the commands and sub-commands along with usage.


### Testing impact
Following test cases should be added
- Set a backend other than `localmongodb` and see of it results in a valid unsupported
  result.
- Set `localmongodb` as backend and execute `planetmint --help` and validate that only the above
  mentioned sub-commands are displayed.


## Implementation

### Assignee(s)
Primary assignee(s): @muawiakh

Secondary assignee(s): @kansi, @ttmc

### Targeted Release
Planetmint 2.0


## Dependencies
N/A


## Reference(s)
* [Bigchaindb CLI](https://docs.planetmint.io/en/latest/tools/index.html#command-line-interface-cli)
