#!/bin/bash
# Copyright © 2020 Interplanetary Database Association e.V.,
# Planetmint and IPDB software contributors.
# SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
# Code is Apache-2.0 and docs are CC-BY-4.0

# Allow root user login
sed -i "s/#PermitRootLogin prohibit-password/PermitRootLogin yes/" /etc/ssh/sshd_config

# Create ssh folder
mkdir ~/.ssh  

# Create ssh keys & publish pukey to shared
ssh-keygen -q -t rsa -N '' -f /shared/${ME}_id_rsa

# Wait for other keys
while [ ! -f /shared/test_id_rsa.pub ]; do
    echo "WAIT FOR PUBKEY"
    sleep 1
done

# Add all pubkeys to authorized keys
cat /shared/test_id_rsa.pub > ~/.ssh/authorized_keys

# Restart ssh service
service ssh restart

exec "$@"