#!/bin/bash
# Copyright © 2020 Interplanetary Database Association e.V.,
# Planetmint and IPDB software contributors.
# SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
# Code is Apache-2.0 and docs are CC-BY-4.0


# MongoDB configuration
# [ "$(stat -c %U /data/db)" = mongodb ] || chown -R mongodb /data/db
# Tarantool configuration
echo STARTING TARANTOOL NOW
tarantool /usr/src/app/scripts/init.lua

# Planetmint configuration
/usr/src/app/scripts/planetmint-monit-config

# nohup mongod --bind_ip_all > "$HOME/.planetmint-monit/logs/mongodb_log_$(date +%Y%m%d_%H%M%S)" 2>&1 &


# Start services
monit -d 5 -I -B