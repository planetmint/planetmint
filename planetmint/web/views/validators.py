# Copyright © 2020 Interplanetary Database Association e.V.,
# Planetmint and IPDB software contributors.
# SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
# Code is Apache-2.0 and docs are CC-BY-4.0

from flask import current_app
from flask_restful import Resource


class ValidatorsApi(Resource):
    def get(self):
        """API endpoint to get validators set.

        Return:
            A JSON string containing the validator set of the current node.
        """

        pool = current_app.config["bigchain_pool"]

        with pool() as planet:
            validators = planet.get_validators()

        return validators
