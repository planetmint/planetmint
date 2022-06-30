#!/bin/bash
# Copyright © 2020 Interplanetary Database Association e.V.,
# Planetmint and IPDB software contributors.
# SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
# Code is Apache-2.0 and docs are CC-BY-4.0

# Planetmint configuration
/usr/src/app/scripts/planetmint-monit-config

# Tarantool startup and configuration
tarantool /usr/src/app/scripts/init.lua

# Start services
monit -d 5 -I -B