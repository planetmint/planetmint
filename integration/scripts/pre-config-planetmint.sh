#!/bin/bash
# Copyright © 2020 Interplanetary Database Association e.V.,
# Planetmint and IPDB software contributors.
# SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
# Code is Apache-2.0 and docs are CC-BY-4.0

# Create ssh folder
mkdir ~/.ssh

# Wait for test container pubkey
while [ ! -f /shared/id_rsa.pub ]; do
    echo "WAIT FOR PUBKEY"
    sleep 1
done

# Add pubkey to authorized keys
cat /shared/id_rsa.pub > ~/.ssh/authorized_keys

# Allow root user login
sed -i "s/#PermitRootLogin prohibit-password/PermitRootLogin yes/" /etc/ssh/sshd_config

# Restart ssh service
service ssh restart

# Tendermint configuration
tendermint init

# Write node id to shared folder
NODE_ID=$(tendermint show_node_id | tail -n 1)
echo $NODE_ID > /shared/${ME}_node_id

# Wait for other node id
while [ ! -f "/shared/${OTHER}_node_id" ]; do
    echo "WAIT FOR NODE ID"
    sleep 1
done

# Write node ids to persistent peers
OTHER_NODE_ID=$(cat /shared/${OTHER}_node_id)
PEERS=$(echo "persistent_peers = \"${NODE_ID}@${ME}:26656, ${OTHER_NODE_ID}@${OTHER}:26656\"")
sed -i "/persistent_peers = \"\"/c\\${PEERS}" /tendermint/config/config.toml

# Copy genesis.json to shared folder
cp /tendermint/config/genesis.json /shared/${ME}_genesis.json

# Await config file of all services to be present
while [ ! -f /shared/${OTHER}_genesis.json ]; do
    echo "WAIT FOR OTHER GENESIS"
    sleep 1
done

# Create genesis.json for nodes
/usr/src/app/scripts/genesis.py

while [ ! -f /shared/genesis.json ]; do
    echo "WAIT FOR GENESIS"
    sleep 1
done

# Copy genesis.json to tendermint config
cp /shared/genesis.json /tendermint/config/genesis.json

exec "$@"