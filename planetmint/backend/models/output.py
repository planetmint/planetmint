# Copyright © 2020 Interplanetary Database Association e.V.,
# Planetmint and IPDB software contributors.
# SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
# Code is Apache-2.0 and docs are CC-BY-4.0

from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class SubCondition:
    type: str
    body: str


@dataclass
class ConditionDetails:
    type: str
    public_key: str = ""
    threshold: int = 0
    sub_conditions: list[SubCondition] = field(default_factory=list)


@dataclass
class Condition:
    uri: str
    details: ConditionDetails


@dataclass
class Output:
    id: str
    amount: int
    condition: field(default_factory=Condition)
    public_keys: str = ""

    @staticmethod
    def from_dict(output: dict, tx_id: str = "") -> Output:
        if output["condition"]["details"].get("subconditions") is None:
            return output_with_public_key(output, tx_id)
        else:
            return output_with_sub_conditions(output, tx_id)

    @staticmethod
    def from_tuple(output: tuple) -> Output:
        return Output(
            id=output[0],
            public_keys=output[1],
            condition=Condition(
                uri=output[2],
                details=ConditionDetails(
                    type=output[3],
                    public_key=output[4],
                    threshold=output[5],
                    sub_conditions=output[6],
                ),
            ),
        )

    def to_output_dict(self) -> dict:
        return {
            "id": self.id,
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


def output_with_sub_conditions(output, tx_id) -> Output:
    return Output(
        id=tx_id,
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


def output_with_public_key(output, tx_id) -> Output:
    return Output(
        id=tx_id,
        amount=output["amount"],
        condition=Condition(
            uri=output["condition"]["uri"],
            details=ConditionDetails(
                type=output["condition"]["details"]["type"],
                public_key=output["condition"]["details"]["public_key"],
            ),
        ),
    )