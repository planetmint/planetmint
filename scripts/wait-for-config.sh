#!/bin/bash
# Copyright © 2020 Interplanetary Database Association e.V.,
# Planetmint and IPDB software contributors.
# SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
# Code is Apache-2.0 and docs are CC-BY-4.0

# Only continue if all files are ready
while [ ! -f /shared/${ME}_genesis.json -o ! -f /shared/${OTHER}_genesis.json ]; do
    echo "SLEEP"
    sleep 1
done

exec "$@"