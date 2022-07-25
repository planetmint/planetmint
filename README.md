<!---
Copyright © 2020 Interplanetary Database Association e.V.,
Planetmint and IPDB software contributors.
SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
Code is Apache-2.0 and docs are CC-BY-4.0
--->

<!--- There is no shield to get the latest version
(including pre-release versions) from PyPI,
so show the latest GitHub release instead.
--->

[![Codecov branch](https://img.shields.io/codecov/c/github/planetmint/planetmint/master.svg)](https://codecov.io/github/planetmint/planetmint?branch=master)
[![Latest release](https://img.shields.io/github/release/planetmint/planetmint/all.svg)](https://github.com/planetmint/planetmint/releases)
[![Status on PyPI](https://img.shields.io/pypi/status/planetmint.svg)](https://pypi.org/project/Planetmint)
[![Build Status](https://app.travis-ci.com/planetmint/planetmint.svg?branch=main)](https://app.travis-ci.com/planetmint/planetmint)
[![Join the chat at https://gitter.im/planetmint/planetmint](https://badges.gitter.im/planetmint/planetmint.svg)](https://gitter.im/planetmint/community?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)

# Planetmint Server

Planetmint is the blockchain database. This repository is for _Planetmint Server_.

## The Basics

* [Try the Quickstart](https://docs.planetmint.io/en/latest/introduction/index.html#quickstart)

## Run and Test Planetmint Server from the `master` Branch

Running and testing the latest version of Planetmint Server is easy. Make sure you have a recent version of [Docker Compose](https://docs.docker.com/compose/install/) installed. When you are ready, fire up a terminal and run:

```text
git clone https://github.com/planetmint/planetmint.git
cd planetmint
make run
```

Planetmint should be reachable now on `http://localhost:9984/`.

There are also other commands you can execute:

* `make start`: Run Planetmint from source and daemonize it (stop it with `make stop`).
* `make stop`: Stop Planetmint.
* `make logs`: Attach to the logs.
* `make lint`: Lint the project
* `make test`: Run all unit and acceptance tests.
* `make test-unit-watch`: Run all tests and wait. Every time you change code, tests will be run again.
* `make cov`: Check code coverage and open the result in the browser.
* `make docs`: Generate HTML documentation and open it in the browser.
* `make clean`: Remove all build, test, coverage and Python artifacts.
* `make reset`: Stop and REMOVE all containers. WARNING: you will LOSE all data stored in Planetmint.

To view all commands available, run `make`.

## Links for Everyone

* [Planetmint.io](https://www.planetmint.io/) - the main Planetmint website, including newsletter signup

## Links for Developers

* [All Planetmint Documentation](https://docs.planetmint.io/en/latest/)
* [CONTRIBUTING.md](.github/CONTRIBUTING.md) - how to contribute
* [Community guidelines](CODE_OF_CONDUCT.md)
* [Open issues](https://github.com/planetmint/planetmint/issues)
* [Open pull requests](https://github.com/planetmint/planetmint/pulls)
* [Gitter chatroom](https://gitter.im/planetmint/planetmint)

## Legal

* [Licenses](LICENSES.md) - open source & open content
