#!/bin/bash
# Copyright © 2020 Interplanetary Database Association e.V.,
# Planetmint and IPDB software contributors.
# SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
# Code is Apache-2.0 and docs are CC-BY-4.0

# Show tendermint node id
show_id () {
    tendermint --home=/tendermint show_node_id | tail -n 1
}

# Show validator public key
show_validator () {
    tendermint --home=/tendermint show_validator | tail -n 1
}

# Elect new voting power for node
elect_validator () {
    planetmint election new upsert-validator $1 $2 $3 --private-key /tendermint/config/priv_validator_key.json 2>&1
}

# Propose new chain migration
propose_migration () {
    planetmint election new chain-migration --private-key /tendermint/config/priv_validator_key.json 2>&1
}

# Show election state
show_election () {
    planetmint election show $1 2>&1
}

# Approve election
approve_validator () {
    planetmint election approve $1 --private-key /tendermint/config/priv_validator_key.json
}

# Fetch tendermint id and pubkey and create upsert proposal
elect () {
    node_id=$(show_id)
    validator_pubkey=$(show_validator | jq -r .value)
    proposal=$(elect_validator $validator_pubkey $1 $node_id | grep SUCCESS)
    echo ${proposal##* }
}

# Create chain migration proposal and return election id
migrate () {
    proposal=$(propose_migration | grep SUCCESS)
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
        migrate )           shift
                            migrate
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