#!/bin/bash
# Copyright © 2020 Interplanetary Database Association e.V.,
# Planetmint and IPDB software contributors.
# SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
# Code is Apache-2.0 and docs are CC-BY-4.0


set -e -x

pip install --upgrade pip

if [[ -n ${TOXENV} ]]; then
    pip install --upgrade tox
elif [[ ${PLANETMINT_CI_ABCI} == 'enable' ]]; then
    docker-compose build --no-cache --build-arg abci_status=enable planetmint
elif [[ $PLANETMINT_INTEGRATION_TEST == 'enable' ]]; then
    docker-compose build planetmint python-driver
else
    docker-compose build --no-cache planetmint
    pip install --upgrade codecov
fi
