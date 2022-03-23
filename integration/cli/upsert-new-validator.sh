#!/bin/bash
# Copyright © 2020 Interplanetary Database Association e.V.,
# Planetmint and IPDB software contributors.
# SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
# Code is Apache-2.0 and docs are CC-BY-4.0

check_status () {
    status=$(ssh -o "StrictHostKeyChecking=no" -i \~/.ssh/id_rsa root@$1 'bash -s' < scripts/election.sh show_election $2 | tail -n 1)
    status=${status#*=}
    if [ $status != $3 ]; then
        exit 1
    fi 
}

# Read host names from shared
readarray -t HOSTNAMES < /shared/hostnames

# Split into proposer and approvers
PROPOSER=${HOSTNAMES[0]}
APPROVERS=${HOSTNAMES[@]:1}

# Propose validator upsert
result=$(ssh -o "StrictHostKeyChecking=no" -i \~/.ssh/id_rsa root@${PROPOSER} 'bash -s' < scripts/election.sh elect 2)

# Check if election is ongoing and approve validator upsert
for APPROVER in ${APPROVERS[@]}; do
    # Check if election is still ongoing
    check_status ${APPROVER} $result ongoing
    ssh -o "StrictHostKeyChecking=no" -i ~/.ssh/id_rsa root@${APPROVER} 'bash -s' < scripts/election.sh approve $result
done

# Status of election should be concluded
check_status ${PROPOSER} $result concluded