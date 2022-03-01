#!/bin/bash
# Copyright © 2020 Interplanetary Database Association e.V.,
# Planetmint and IPDB software contributors.
# SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
# Code is Apache-2.0 and docs are CC-BY-4.0

# Create ssh folder
mkdir ~/.ssh

# Create ssh keys
ssh-keygen -q -t rsa -N '' -f ~/.ssh/id_rsa

# Publish pubkey to shared folder
cp ~/.ssh/id_rsa.pub /shared

exec "$@"