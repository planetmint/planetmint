#!/bin/bash
# Copyright © 2020 Interplanetary Database Association e.V.,
# Planetmint and IPDB software contributors.
# SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
# Code is Apache-2.0 and docs are CC-BY-4.0

# Read host names from shared
readarray -t HOSTNAMES < /shared/hostnames

# Split into proposer and approvers
ALPHA=${HOSTNAMES[0]}
BETAS=${HOSTNAMES[@]:1}

# Propose validator upsert
result=$(ssh -o "StrictHostKeyChecking=no" -i \~/.ssh/id_rsa root@${ALPHA} 'bash -s' < scripts/election.sh elect 2)

# Approve validator upsert
for BETA in ${BETAS[@]}; do
    ssh -o "StrictHostKeyChecking=no" -i ~/.ssh/id_rsa root@${BETA} 'bash -s' < scripts/election.sh approve $result
done

exec "$@"