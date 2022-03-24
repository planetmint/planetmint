#!/bin/bash
# Copyright © 2020 Interplanetary Database Association e.V.,
# Planetmint and IPDB software contributors.
# SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
# Code is Apache-2.0 and docs are CC-BY-4.0

# Start CLI Tests

# Test upsert new validator
/tests/upsert-new-validator.sh

# Test chain migration
# TODO: implementation not finished
#/tests/chain-migration.sh

# TODO: Implement test for voting edge cases or implicit in chain migration and upsert validator?

exitcode=$?

if [ $exitcode -ne 0 ]; then
    exit $exitcode
fi

exec "$@"