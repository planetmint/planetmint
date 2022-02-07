#!/usr/bin/env bash
# Copyright © 2020 Interplanetary Database Association e.V.,
# Planetmint and IPDB software contributors.
# SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
# Code is Apache-2.0 and docs are CC-BY-4.0


# Check if both integration test nodes are reachable
check_status () {
    OK="200 OK"

    STATUS_1=$(curl -I -s -X GET https://itest1.planetmint.io/ | head -n 1)
    STATUS_2=$(curl -I -s -X GET https://itest2.planetmint.io/ | head -n 1)

    # Check if both response status codes return 200 OK
    if ! [[ "$STATUS_1" == *"$OK"* ]] || ! [[ "$STATUS_2" == *"$OK"* ]]
    then
        exit 1
    fi
}

run_test () {
	docker-compose run --rm python-integration pytest /src
}

teardown () {
	docker-compose down
}

check_status
run_test
exitcode=$?
teardown

exit $exitcode