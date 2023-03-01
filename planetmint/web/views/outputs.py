# Copyright © 2020 Interplanetary Database Association e.V.,
# Planetmint and IPDB software contributors.
# SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
# Code is Apache-2.0 and docs are CC-BY-4.0

from flask import current_app
from flask_restful import reqparse, Resource
from planetmint.web.views import parameters
from planetmint.web.views.base import make_error


class OutputListApi(Resource):
    def get(self):
        """API endpoint to retrieve a list of links to transaction
        outputs.

            Returns:
                A :obj:`list` of :cls:`str` of links to outputs.
        """
        parser = reqparse.RequestParser()
        parser.add_argument("public_key", type=parameters.valid_ed25519, required=True)
        parser.add_argument("spent", type=parameters.valid_bool)
        args = parser.parse_args(strict=True)

        validator_class = current_app.config["validator_class_name"]
        with validator_class() as validator:
            try:
                outputs = validator.models.get_outputs_filtered(args["public_key"], args["spent"])
            except Exception as e:
                return make_error(
                    500,
                    "Invalid output ({}): {} : {} - {}".format(type(e).__name__, e, args["public_key"], args["spent"]),
                    level="error",
                )
            return [{"transaction_id": output.txid, "output_index": output.output} for output in outputs]
