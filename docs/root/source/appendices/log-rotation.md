<!---
Copyright © 2020 Interplanetary Database Association e.V.,
Planetmint and IPDB software contributors.
SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
Code is Apache-2.0 and docs are CC-BY-4.0
--->

# Logging and Log Rotation

Each Planetmint node runs:

- Tarantool
- Planetmint Server
- Tendermint

When running a Planetmint node for long periods
of time, we need to consider doing log rotation, i.e. we do not want the logs taking
up large amounts of storage and making the node unresponsive or getting it into a bad state.


## Planetmint Server Logging and Log Rotation

Planetmint Server writes its logs to two files: normal logs and error logs. The names of those files, and their locations, are set as part of the Planetmint configuration settings. The default names and locations are:

- `~/planetmint.log`
- `~/planetmint-errors.log`

Log rotation is baked into Planetmint Server using Python's `logging` module. The logs for Planetmint Server are rotated when any of the above mentioned files exceeds 209715200 bytes (i.e. approximately 209 MB).

For more information, see the docs about [the Planetmint Server configuration settings related to logging](../node-setup/configuration#log).

## Tendermint Logging and Log Rotation

Tendermint writes its logs to the files:

- `tendermint.out.log`
- `tendermint.err.log`

If you started Planetmint Server and Tendermint using Monit, as suggested by our guide on
[How to Set Up a Planetmint Network](../network-setup/network-setup),
then the logs will be written to `$HOME/.planetmint-monit/logs/`.

Moreover, if you started Planetmint Server and Tendermint using Monit,
then Monit monitors the Tendermint log files.
Tendermint logs are rotated if any of the above mentioned log files exceeds 200 MB.
