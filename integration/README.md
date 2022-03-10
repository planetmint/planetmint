<!---
Copyright © 2020 Interplanetary Database Association e.V.,
Planetmint and IPDB software contributors.
SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
Code is Apache-2.0 and docs are CC-BY-4.0
--->

# Integration test suite
This directory contains the integration test suite for Planetmint.

The suite uses Docker Compose to spin up multiple Planetmint nodes, run tests with `pytest` as well as cli tests and teardown. 

## Running the tests
Run `make test-integration` in the project root directory.

By default the integration test suite spins up four planetmint nodes. If you desire to run a different configuration you can pass `SCALE=<number of nodes>` as an environmental variable.

## Writing and documenting the tests
Tests are sometimes difficult to read. For integration tests, we try to be really explicit on what the test is doing, so please write code that is *simple* and easy to understand. We decided to use literate-programming documentation. To generate the documentation for python tests run:

```bash
make docs-integration
```
