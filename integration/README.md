<!---
Copyright © 2020 Interplanetary Database Association e.V.,
Planetmint and IPDB software contributors.
SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
Code is Apache-2.0 and docs are CC-BY-4.0
--->

# Integration test suite
This directory contains the integration test suite for Planetmint.

The suite uses Docker Compose to run all tests.

## Running the tests
Run `make test-integration` in the project root directory.

During development you can run single test use `pytest` inside the `python-integration` container with:

```bash
docker-compose run --rm python-integration pytest <use whatever option you need>
```

Note: The `/src` directory contains all the test within the container.
