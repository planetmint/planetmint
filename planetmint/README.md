<!---
Copyright © 2020 Interplanetary Database Association e.V.,
Planetmint and IPDB software contributors.
SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
Code is Apache-2.0 and docs are CC-BY-4.0
--->

# Overview

A high-level description of the files and subdirectories of Planetmint.

## Files

### [`lib.py`](lib.py)

The `Planetmint` class is defined here.  Most node-level operations and database interactions are found in this file.  This is the place to start if you are interested in implementing a server API, since many of these class methods concern Planetmint interacting with the outside world.

### [`models.py`](./models.py)

`Block`, `Transaction`, and `Asset` classes are defined here.  The classes mirror the block and transaction structure from the documentation, but also include methods for validation and signing.

### [`validation.py`](application/basevalidationrules.py)

Base class for validation methods (verification of votes, blocks, and transactions).  The actual logic is mostly found in `transaction` and `block` models, defined in [`models.py`](./models.py).

### [`processes.py`](./processes.py)

Entry point for the Planetmint process, after initialization.  All subprocesses are started here: processes to handle new blocks, votes, etc.

### [`config_utils.py`](config_utils.py)

Methods for managing the configuration, including loading configuration files, automatically generating the configuration, and keeping the configuration consistent across Planetmint instances.

## Folders

### [`commands`](./commands)

Contains code for the [CLI](https://docs.planetmint.io/en/latest/tools/index.html#command-line-interface-cli) for Planetmint.

### [`db`](./db)

Code for building the database connection, creating indexes, and other database setup tasks.
