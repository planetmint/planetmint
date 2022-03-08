#!/bin/bash
# Copyright © 2020 Interplanetary Database Association e.V.,
# Planetmint and IPDB software contributors.
# SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
# Code is Apache-2.0 and docs are CC-BY-4.0

# Only continue if all services are ready
HOSTNAMES=()
while [ ! ${#HOSTNAMES[@]} == $SCALE ]; do
    echo "WAIT FOR HOSTNAMES"
    sleep 1
    readarray -t HOSTNAMES < /shared/hostnames
done

for host in ${HOSTNAMES[@]}; do
    while [[ "$(curl -s -o /dev/null -w ''%{http_code}'' $host:9984)" != "200" ]]; do
        echo "WAIT FOR PLANETMINT $host"
        sleep 1
    done
done

for host in ${HOSTNAMES[@]}; do
    while [[ "$(curl -s -o /dev/null -w ''%{http_code}'' $host:26657)" != "200" ]]; do
        echo "WAIT FOR TENDERMINT $host"
        sleep 1
    done
done

exec "$@"