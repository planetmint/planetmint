#!/bin/bash
# Copyright © 2020 Interplanetary Database Association e.V.,
# Planetmint and IPDB software contributors.
# SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
# Code is Apache-2.0 and docs are CC-BY-4.0


set -e -x

if [[ -n ${TOXENV} ]]; then
  tox -e ${TOXENV}
elif [[ ${PLANETMINT_CI_ABCI} == 'enable' ]]; then
  docker-compose exec planetmint pytest -v -m abci
elif [[ ${PLANETMINT_ACCEPTANCE_TEST} == 'enable' ]]; then
    ./run-acceptance-test.sh
elif [[ ${PLANETMINT_INTEGRATION_TEST} == 'enable' ]]; then
    chmod 600 id_ed25519
    # ./run-integration-test.sh
    ./scripts/test.sh
else
  docker-compose exec planetmint pytest -v --cov=planetmint --cov-report xml:htmlcov/coverage.xml
fi
