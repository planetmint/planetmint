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
