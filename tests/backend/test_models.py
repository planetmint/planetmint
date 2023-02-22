# Copyright © 2020 Interplanetary Database Association e.V.,
# Planetmint and IPDB software contributors.
# SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
# Code is Apache-2.0 and docs are CC-BY-4.0

from planetmint.backend.models import Output

nested_threshold_output = {
    "amount": "1",
    "condition": {
        "details": {
            "subconditions": [
                {"type": "ed25519-sha-256", "public_key": "7pT7eBEGJsmpUvRFhu7NUQSZVJVZDeF1xREuYKdVYUKK"},
                {
                    "subconditions": [
                        {"type": "ed25519-sha-256", "public_key": "746ZbyMgoCJykAdzZ2vZcHzwnndrVnAAh6pv6yLZDiH2"},
                        {"type": "ed25519-sha-256", "public_key": "EYb188vCQoaYDmW3Agen1u6Fh7xvDWCMnWJK8ueuCdbX"},
                    ],
                    "threshold": 2,
                    "type": "threshold-sha-256",
                },
            ],
            "threshold": 1,
            "type": "threshold-sha-256",
        },
        "uri": "ni:///sha-256;hhw6Rf9JgwKYkapwE9qu7oVaI0ArS0hj_dmzAkpIPdc?fpt=threshold-sha-256&cost=266240&subtypes=ed25519-sha-256",
    },
    "public_keys": [
        "7pT7eBEGJsmpUvRFhu7NUQSZVJVZDeF1xREuYKdVYUKK",
        "746ZbyMgoCJykAdzZ2vZcHzwnndrVnAAh6pv6yLZDiH2",
        "EYb188vCQoaYDmW3Agen1u6Fh7xvDWCMnWJK8ueuCdbX",
    ],
}


def test_output_nested_threshold_condition():
    output = Output.outputs_dict(nested_threshold_output)
    assert output
    output_dict = output.to_dict()
    assert nested_threshold_output == output_dict
