#!/bin/bash
# Copyright © 2020 Interplanetary Database Association e.V.,
# Planetmint and IPDB software contributors.
# SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
# Code is Apache-2.0 and docs are CC-BY-4.0


set -e -x

if [[ -z ${TOXENV} ]]; then

  if [[ ${PLANETMINT_CI_ABCI} == 'enable' ]]; then
      docker-compose up -d planetmint
  else
      docker-compose up -d bdb
  fi

fi
