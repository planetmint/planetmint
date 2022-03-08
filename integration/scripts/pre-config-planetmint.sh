#!/bin/bash
# Copyright © 2020 Interplanetary Database Association e.V.,
# Planetmint and IPDB software contributors.
# SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
# Code is Apache-2.0 and docs are CC-BY-4.0

# Write hostname to list
echo $(hostname) >> /shared/hostnames

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
HOSTNAME=$(hostname)
NODE_ID=$(tendermint show_node_id | tail -n 1)
echo $NODE_ID > /shared/${HOSTNAME}_node_id

# Wait for other node ids
FILES=()
while [ ! ${#FILES[@]} == $SCALE ]; do
    echo "WAIT FOR NODE IDS"
    sleep 1
    FILES=(/shared/*node_id)
done

# Write node ids to persistent peers
PEERS="persistent_peers = \""
for f in ${FILES[@]}; do
    ID=$(cat $f)
    HOST=$(echo $f | cut -c 9-20)
    if [ ! $HOST == $HOSTNAME ]; then
        PEERS+="${ID}@${HOST}:26656, "
    fi
done
PEERS=$(echo $PEERS | rev | cut -c 2- | rev)
PEERS+="\""
sed -i "/persistent_peers = \"\"/c\\${PEERS}" /tendermint/config/config.toml

# Copy genesis.json to shared folder
cp /tendermint/config/genesis.json /shared/${HOSTNAME}_genesis.json

# Await config file of all services to be present
FILES=()
while [ ! ${#FILES[@]} == $SCALE ]; do
    echo "WAIT FOR GENESIS FILES"
    sleep 1
    FILES=(/shared/*_genesis.json)
done

# Create genesis.json for nodes
if [ ! -f /shared/lock ]; then
    echo LOCKING
    touch /shared/lock
    /usr/src/app/scripts/genesis.py ${FILES[@]}
fi

while [ ! -f /shared/genesis.json ]; do
    echo "WAIT FOR GENESIS"
    sleep 1
done

# Copy genesis.json to tendermint config
cp /shared/genesis.json /tendermint/config/genesis.json

exec "$@"