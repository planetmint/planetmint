#!/bin/bash
# Copyright © 2020 Interplanetary Database Association e.V.,
# Planetmint and IPDB software contributors.
# SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
# Code is Apache-2.0 and docs are CC-BY-4.0

# Change user and activate virtualenv
activate () {
    cd /home/bigchaindb
    source env/bigchaindb/bin/activate
}

# Show tendermint node id
show_id () {
    su tendermint -c "cd && go/bin/tendermint show_node_id"
}

# Show validator public key
show_validator () {
    su tendermint -c "cd && go/bin/tendermint show_validator"
}

# Elect new voting power for node
elect_validator () {
    activate
    bigchaindb election new upsert-validator $1 $2 $3 --private-key /tmp/priv_validator_key.json
}

# Show election state
show_election () {
    activate
    bigchaindb election show $1
}

# Approve election
approve_validator () {
    activate
    bigchaindb election approve $1 --private-key /tmp/priv_validator_key.json
}

# Fetch tendermint id and pubkey and create upsert proposal
elect () {
    node_id=$(show_id)
    validator_pubkey=$(show_validator | jq -r .value)
    proposal=$(elect_validator $validator_pubkey $1 $node_id 2>&1 | grep SUCCESS)
    echo ${proposal##* }
}

usage () {
    echo "usage: TODO"
}
 
while [ "$1" != "" ]; do
    case $1 in
        show_id )           show_id
                            ;;
        show_validator )    show_validator
                            ;;
        elect )             shift
                            elect $1
                            ;;
        show_election )     shift
                            show_election $1
                            ;;
        approve )           shift
                            approve_validator $1
                            ;;
        * )                 usage
                            exit 1                           
    esac
    shift
done

exitcode=$?

exit $exitcode