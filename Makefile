.PHONY: help run start stop logs lint test test-unit test-unit-watch test-acceptance test-integration cov docs docs-acceptance clean reset release dist check-deps clean-build clean-pyc clean-test

.DEFAULT_GOAL := help


#############################
# Open a URL in the browser #
#############################
define BROWSER_PYSCRIPT
import os, webbrowser, sys
try:
	from urllib import pathname2url
except:
	from urllib.request import pathname2url

webbrowser.open("file://" + pathname2url(os.path.abspath(sys.argv[1])))
endef
export BROWSER_PYSCRIPT


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
BROWSER := python -c "$$BROWSER_PYSCRIPT"
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
	# although planetmint has tendermint and mongodb in depends_on,
	# launch them first otherwise tendermint will get stuck upon sending yet another log
	# due to some docker-compose issue; does not happen when containers are run as daemons
	@$(DC) up --no-deps mongodb tendermint planetmint

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

test: check-deps test-unit test-acceptance ## Run unit and acceptance tests

test-unit: check-deps ## Run all tests once
	@$(DC) up -d bdb
	@$(DC) exec planetmint pytest ${TEST}

test-unit-watch: check-deps ## Run all tests and wait. Every time you change code, tests will be run again
	@$(DC) run --rm --no-deps planetmint pytest -f

test-acceptance: check-deps ## Run all acceptance tests
	@./scripts/run-acceptance-test.sh

test-integration: check-deps ## Run all integration tests
	@./scripts/run-integration-test.sh

cov: check-deps ## Check code coverage and open the result in the browser
	@$(DC) run --rm planetmint pytest -v --cov=planetmint --cov-report html
	$(BROWSER) htmlcov/index.html

docs: check-deps ## Generate HTML documentation and open it in the browser
	@$(DC) run --rm --no-deps bdocs make -C docs/root html
	$(BROWSER) docs/root/build/html/index.html

docs-acceptance: check-deps ## Create documentation for acceptance tests
	@$(DC) run --rm python-acceptance pycco -i -s /src -d /docs
	$(BROWSER) acceptance/python/docs/index.html

docs-integration: check-deps ## Create documentation for integration tests
	@$(DC) run --rm python-integration pycco -i -s /src -d /docs
	$(BROWSER) integration/python/docs/index.html

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