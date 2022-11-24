# Copyright © 2020 Interplanetary Database Association e.V.,
# Planetmint and IPDB software contributors.
# SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
# Code is Apache-2.0 and docs are CC-BY-4.0

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List

from planetmint.backend.models.keys import Keys


@dataclass
class SubCondition:
    type: str
    body: str


@dataclass
class ConditionDetails:
    type: str = ""
    public_key: str = ""
    threshold: int = 0
    sub_conditions: list[SubCondition] = None


@dataclass
class Condition:
    uri: str = ""
    details: ConditionDetails = field(default_factory=ConditionDetails)


@dataclass
class Output:
    tx_id: str = ""
    amount: int = 0
    public_keys: List[str] = field(default_factory=list)
    condition: Condition = field(default_factory=Condition)

    @staticmethod
    def outputs_and_keys_dict(output: dict, tx_id: str = "") -> (Output, Keys):
        out_dict: Output
        if output["condition"]["details"].get("subconditions") is None:
            out_dict = output_with_public_key(output, tx_id)
        else:
            out_dict = output_with_sub_conditions(output, tx_id)
        return out_dict, Keys.from_dict(output, tx_id)

    @staticmethod
    def from_tuple(output: tuple) -> Output:
        return Output(
            tx_id=output[0],
            condition=Condition(
                uri=output[1],
                details=ConditionDetails(
                    type=output[2],
                    public_key=output[3],
                    threshold=output[4],
                    sub_conditions=output[5],
                ),
            ),
        )

    def to_output_dict(self) -> dict:
        return {
            "id": self.tx_id,
            "amount": self.amount,
            "public_keys": self.public_keys,
            "condition": {
                "uri": self.condition.uri,
                "details": {
                    "type": self.condition.details.type,
                    "public_key": self.condition.details.public_key,
                    "threshold": self.condition.details.threshold,
                    "subconditions": self.condition.details.sub_conditions,
                },
            },
        }


def output_with_public_key(output, tx_id) -> Output:
    return Output(
        tx_id=tx_id,
        public_keys=output["public_keys"],
        amount=output["amount"],
        condition=Condition(
            uri=output["condition"]["uri"],
            details=ConditionDetails(
                type=output["condition"]["details"]["type"],
                public_key=output["condition"]["details"]["public_key"],
            ),
        ),
    )


def output_with_sub_conditions(output, tx_id) -> Output:
    return Output(
        tx_id=tx_id,
        public_keys=output["public_keys"],
        amount=output["amount"],
        condition=Condition(
            uri=output["condition"]["uri"],
            details=ConditionDetails(
                type=output["condition"]["details"]["type"],
                threshold=output["condition"]["details"]["threshold"],
                sub_conditions=[
                    SubCondition(
                        type=sub_condition["type"],
                        body=sub_condition["body"],
                    )
                    for sub_condition in output["condition"]["details"][
                        "subconditions"
                    ]
                ],
            ),
        ),
    )



