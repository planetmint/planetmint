#!/bin/bash
# Copyright © 2020 Interplanetary Database Association e.V.,
# Planetmint and IPDB software contributors.
# SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
# Code is Apache-2.0 and docs are CC-BY-4.0


# MongoDB configuration
[ "$(stat -c %U /data/db)" = mongodb ] || chown -R mongodb /data/db

# Planetmint configuration
planetmint-monit-config

nohup mongod --bind_ip_all > "$HOME/.planetmint-monit/logs/mongodb_log_$(date +%Y%m%d_%H%M%S)" 2>&1 &

# Tendermint configuration
tendermint init

sleep 1

NODE_ID=$(tendermint show_node_id | tail -n 1)

if [ ! -f "/shared/${ME}_node_id" ]; then
    touch /shared/${ME}_node_id
fi

echo $NODE_ID > /shared/${ME}_node_id
cp /tendermint/config/genesis.json /shared/${ME}_genesis.json

for i in $(seq 3); do
    if [ -f "/shared/${OTHER}_node_id" ]; then
        OTHER_NODE_ID=$(cat /shared/${OTHER}_node_id)
        PEERS=$(echo "persistent_peers = \"${NODE_ID}@${ME}:26656, ${OTHER_NODE_ID}@${OTHER}:26656\"")
        sed -i "/persistent_peers = \"\"/c\\${PEERS}" /tendermint/config/config.toml
        break
    else
        sleep 1
    fi
done

/usr/src/app/scripts/genesis.py

cp /shared/planetmint_1_genesis.json /tendermint/config/genesis.json 

monit -d 5 -I -B