#!/bin/sh
# Copyright © 2020 Interplanetary Database Association e.V.,
# Planetmint and IPDB software contributors.
# SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
# Code is Apache-2.0 and docs are CC-BY-4.0

cd planetmint

# Remove build artifacts
rm -fr build/
rm -fr dist/
rm -fr .eggs/
find . -name '*.egg-info' -exec rm -fr {} +
find . -name '*.egg' -type f -exec rm -f {} +

# Remove Python file artifacts
find . -name '*.pyc' -exec rm -f {} +
find . -name '*.pyo' -exec rm -f {} +
find . -name '*~' -exec rm -f {} +
find . -name '__pycache__' -exec rm -fr {} +

# Remove test and coverage artifacts
find . -name '.pytest_cache' -exec rm -fr {} +
rm -fr .tox/
rm -f .coverage
rm -fr htmlcov/