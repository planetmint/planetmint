.PHONY: help run start stop logs lint test test-unit test-unit-watch test-integration cov docs clean reset release dist check-deps clean-build clean-pyc clean-test

.DEFAULT_GOAL := help


##################################
# Display help for this makefile #
##################################
define PRINT_HELP_PYSCRIPT
import re, sys

print("Planetmint 2.0 developer toolbox")
print("--------------------------------")
print("Usage:  make COMMAND")
print("")
print("Commands:")
for line in sys.stdin:
	match = re.match(r'^([a-zA-Z_-]+):.*?## (.*)$$', line)
	if match:
		target, help = match.groups()
		print("    %-16s %s" % (target, help))
endef
export PRINT_HELP_PYSCRIPT

##################
# Basic commands #
##################
DOCKER := docker
DC := docker-compose
HELP := python -c "$$PRINT_HELP_PYSCRIPT"
ECHO := /usr/bin/env echo

IS_DOCKER_COMPOSE_INSTALLED := $(shell command -v docker-compose 2> /dev/null)
IS_BLACK_INSTALLED := $(shell command -v black 2> /dev/null)

################
# Main targets #
################

help: ## Show this help
	@$(HELP) < $(MAKEFILE_LIST)

run: check-deps ## Run Planetmint from source (stop it with ctrl+c)
	# although planetmint has tendermint and tarantool in depends_on,
	# launch them first otherwise tendermint will get stuck upon sending yet another log
	# due to some docker-compose issue; does not happen when containers are run as daemons
	@$(DC) up --no-deps tarantool tendermint planetmint

start: check-deps ## Run Planetmint from source and daemonize it (stop with `make stop`)
	@$(DC) up -d planetmint

stop: check-deps ## Stop Planetmint
	@$(DC) stop

logs: check-deps ## Attach to the logs
	@$(DC) logs -f planetmint

lint: check-py-deps ## Lint the project
	black --check -l 119 .

format: check-py-deps ## Format the project
	black -l 119 .

test: check-deps test-unit  ## Run unit 

test-unit: check-deps ## Run all tests once or specify a file/test with TEST=tests/file.py::Class::test
	@$(DC) up -d tarantool
	#wget https://github.com/tendermint/tendermint/releases/download/v0.34.15/tendermint_0.34.15_linux_amd64.tar.gz
	#tar zxf tendermint_0.34.15_linux_amd64.tar.gz
	poetry run pytest -m "not abci"
	rm -rf ~/.tendermint && ./tendermint init && ./tendermint node --consensus.create_empty_blocks=false --rpc.laddr=tcp://0.0.0.0:26657 --proxy_app=tcp://localhost:26658&
	poetry run pytest -m abci
	@$(DC) down



test-unit-watch: check-deps ## Run all tests and wait. Every time you change code, tests will be run again
	@$(DC) run --rm --no-deps planetmint pytest -f



test-integration: check-deps ## Run all integration tests
	@./scripts/run-integration-test.sh

cov: check-deps ## Check code coverage and open the result in the browser
	@$(DC) run --rm planetmint pytest -v --cov=planetmint --cov-report html

docs: check-deps ## Generate HTML documentation and open it in the browser
	@$(DC) run --rm --no-deps bdocs make -C docs/root html

clean: check-deps ## Remove all build, test, coverage and Python artifacts
	@$(DC) up clean
	@$(ECHO) "Cleaning was successful."

reset: check-deps ## Stop and REMOVE all containers. WARNING: you will LOSE all data stored in Planetmint.
	@$(DC) down

release: dist ## package and upload a release
	twine upload dist/*

dist: clean ## builds source (and not for now, wheel package)
	python setup.py sdist
	# python setup.py bdist_wheel
	ls -l dist

###############
# Sub targets #
###############

check-deps:
ifndef IS_DOCKER_COMPOSE_INSTALLED
	@$(ECHO) "Error: docker-compose is not installed"
	@$(ECHO)
	@$(ECHO) "You need docker-compose to run this command. Check out the official docs on how to install it in your system:"
	@$(ECHO) "- https://docs.docker.com/compose/install/"
	@$(ECHO)
	@$(DC) # docker-compose is not installed, so we call it to generate an error and exit
endif

check-py-deps:
ifndef IS_BLACK_INSTALLED
	@$(ECHO) "Error: black is not installed"
	@$(ECHO)
	@$(ECHO) "You need to activate your virtual environment and install the test dependencies"
	black # black is not installed, so we call it to generate an error and exit
endif

