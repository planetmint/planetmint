#!/bin/bash
# Copyright © 2020 Interplanetary Database Association e.V.,
# Planetmint and IPDB software contributors.
# SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
# Code is Apache-2.0 and docs are CC-BY-4.0

# Only continue if all services are ready

# TODO: Ping planetmint 9984 and tendermint 26657
while [[ "$(curl -s -o /dev/null -w ''%{http_code}'' planetmint_1:9984/api/v1)" != "200" ]]; do
    echo "WAIT FOR PLANETMINT"
    sleep 1
done

while [[ "$(curl -s -o /dev/null -w ''%{http_code}'' planetmint_1:26657)" != "200" ]]; do
    echo "WAIT FOR TENDERMINT"
    sleep 1
done

exec "$@"