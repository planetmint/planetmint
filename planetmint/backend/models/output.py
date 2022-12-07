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
    public_key: str

    def to_tuple(self) -> tuple:
        return self.type, self.public_key

    @staticmethod
    def from_dict(subcondition_dict: dict) -> SubCondition:
        return SubCondition(subcondition_dict["type"], subcondition_dict["public_key"])

@dataclass
class ConditionDetails:
    type: str = ""
    public_key: str = ""
    threshold: int = 0
    sub_conditions: list[SubCondition] = None

    @staticmethod
    def from_dict(data: dict) -> ConditionDetails:
        sub_conditions = None
        if data["sub_conditions"] is not None:
            sub_conditions = [SubCondition.from_dict(sub_condition) for sub_condition in data["sub_conditions"]]
        return ConditionDetails(
            type=data.get("type"),
            public_key=data.get("public_key"),
            threshold=data.get("threshold"),
            sub_conditions=sub_conditions,
        )

@dataclass
class Condition:
    uri: str = ""
    details: ConditionDetails = field(default_factory=ConditionDetails)


    @staticmethod
    def from_dict(data: dict) -> Condition:
        return Condition(
            uri=data.get("uri"),
            details=ConditionDetails.from_dict(data.get("details")),
        )

    def to_dict(self) -> dict:
        return {
            "uri": self.uri,
            "details": self.details.__dict__,
        }

    @staticmethod
    def list_of_sub_conditions_to_tuple(sub_conditions: List[SubCondition]) -> tuple:
        sub_con_tuple = None
        if sub_conditions is not None:
            sub_con_tuple = [sub_condition.to_tuple() for sub_condition in sub_conditions]
        return sub_con_tuple

@dataclass
class Output:
    id: str = ""
    amount: int = 0
    transaction_id: str = ""
    public_keys: List[str] = field(default_factory=list)
    index: int = 0
    condition: Condition = field(default_factory=Condition)

    @staticmethod
    def outputs_dict(output: dict, transaction_id: str = "") -> Output:
        out_dict: Output
        if output["condition"]["details"].get("subconditions") is None:
            out_dict = output_with_public_key(output, transaction_id)
        else:
            out_dict = output_with_sub_conditions(output, transaction_id)
        return out_dict

    @staticmethod
    def from_tuple(output: tuple) -> Output:
        return Output(
            id=output[0],
            amount=output[1],
            public_keys=output[2],
            condition=Condition.from_dict(
                output[3],
            ),
            index=output[4],
            transaction_id=output[5],
        )

    def to_dict(self) -> dict:
        return {
            "id": self.transaction_id,
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


    @staticmethod
    def list_to_dict(output_list: list[Output]) -> list[dict]:
        return [output.to_dict() for output in output_list or []]


def output_with_public_key(output, transaction_id) -> Output:
    return Output(
        transaction_id=transaction_id,
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


def output_with_sub_conditions(output, transaction_id) -> Output:
    return Output(
        transaction_id=transaction_id,
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
                        public_key=sub_condition["public_key"],
                    )
                    for sub_condition in output["condition"]["details"]["subconditions"]
                ],
            ),
        ),
    )
