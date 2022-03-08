#!/bin/bash
# Copyright © 2020 Interplanetary Database Association e.V.,
# Planetmint and IPDB software contributors.
# SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
# Code is Apache-2.0 and docs are CC-BY-4.0

run_test() {
    docker-compose -f docker-compose.integration.yml up test
}

teardown () {
    docker-compose -f docker-compose.integration.yml down
}

run_test
exitcode=$?
teardown

exit $exitcode