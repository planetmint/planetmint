<!---
Copyright © 2020 Interplanetary Database Association e.V.,
Planetmint and IPDB software contributors.
SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
Code is Apache-2.0 and docs are CC-BY-4.0
--->

# Planetmint Server Unit Tests

Most of the tests in the `tests/` folder are unit tests. For info about how to write and run tests, see [the docs about contributing to Planetmint](http://docs.planetmint.com/projects/contributing/en/latest/index.html), especially:

- [Write Code - Remember to Write Tests](http://docs.planetmint.com/projects/contributing/en/latest/dev-setup-coding-and-contribution-process/write-code.html#remember-to-write-tests)
- [Notes on Running a Local Dev Node with Docker Compose](http://docs.planetmint.com/projects/contributing/en/latest/dev-setup-coding-and-contribution-process/run-node-with-docker-compose.html), especially `make test`
- [
Notes on Running a Local Dev Node as Processes (and Running All Tests)](http://docs.planetmint.com/projects/contributing/en/latest/dev-setup-coding-and-contribution-process/run-node-as-processes.html)

Note: There are acceptance tests in the `acceptance/` folder (at the same level in the hierarchy as the `tests/` folder).

## Debugging test cases with VS Code

In order to debug unit tests create a virtual environment and install all necessary dependencies. VS Code should notify you that a new virtual environment is detected and ask if you want to use it as environment (more info: [Getting started with Python in VS Code](https://code.visualstudio.com/docs/python/python-tutorial)).

Configure the tests in VS Code by goint to the `Testing` tab and click `Confiugre Python Tests` and select `pytest`. VS Code should now detect all test cases inside of `tests`. Click `Debug Tests` to run the tests with the debugger attached. (more info: [Python testing in VS Code](https://code.visualstudio.com/docs/python/testing))

Note: `pip install .` will not automatically install the test dependencies. If missing install them manually.