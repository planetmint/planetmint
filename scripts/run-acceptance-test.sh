#!/usr/bin/env bash
# Copyright © 2020 Interplanetary Database Association e.V.,
# Planetmint and IPDB software contributors.
# SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
# Code is Apache-2.0 and docs are CC-BY-4.0


# Set up a Planetmint node and return only when we are able to connect to both
# the Planetmint container *and* the Tendermint container.
setup () {
	docker-compose up -d planetmint

	# Try to connect to the containers for maximum three times, and wait
	# one second between tries.
	for i in $(seq 3); do
		if $(docker-compose run --rm curl-client); then
			break
		else
			sleep 1
		fi
	done
}

run_test () {
	docker-compose run --rm python-acceptance pytest /src
}

teardown () {
	docker-compose down
}

setup
run_test
exitcode=$?
teardown

exit $exitcode
