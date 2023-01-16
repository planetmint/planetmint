# Copyright © 2020 Interplanetary Database Association e.V.,
# Planetmint and IPDB software contributors.
# SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
# Code is Apache-2.0 and docs are CC-BY-4.0

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List


@dataclass
class SubCondition:
    type: str
    public_key: str

    def to_tuple(self) -> tuple:
        return self.type, self.public_key

    def to_dict(self) -> dict:
        return {"type": self.type, "public_key": self.public_key}

    @staticmethod
    def from_dict(subcondition_dict: dict) -> SubCondition:
        return SubCondition(subcondition_dict["type"], subcondition_dict["public_key"])

    @staticmethod
    def list_to_dict(subconditions: List[SubCondition]) -> List[dict] | None:
        if subconditions is None:
            return None
        return [subcondition.to_dict() for subcondition in subconditions]


@dataclass
class ConditionDetails:
    type: str = ""
    public_key: str = ""
    threshold: int = None
    sub_conditions: list[SubCondition] = None

    def to_dict(self) -> dict:
        if self.sub_conditions is None:
            return {
                "type": self.type,
                "public_key": self.public_key,
            }
        else:
            return {
                "type": self.type,
                "threshold": self.threshold,
                "subconditions": [subcondition.to_dict() for subcondition in self.sub_conditions],
            }

    @staticmethod
    def from_dict(data: dict) -> ConditionDetails:
        sub_conditions = None
        if "subconditions" in data:
            sub_conditions = [SubCondition.from_dict(sub_condition) for sub_condition in data["subconditions"]]
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
            "details": self.details.to_dict(),
        }


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

    @staticmethod
    def from_dict(output_dict: dict, index: int, transaction_id: str) -> Output:
        return Output(
            id=output_dict["id"] if "id" in output_dict else "placeholder",
            amount=int(output_dict["amount"]),
            public_keys=output_dict["public_keys"],
            condition=Condition.from_dict(output_dict["condition"]),
            index=index,
            transaction_id=transaction_id,
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "public_keys": self.public_keys,
            "condition": {
                "details": {
                    "type": self.condition.details.type,
                    "public_key": self.condition.details.public_key,
                    "threshold": self.condition.details.threshold,
                    "subconditions": SubCondition.list_to_dict(self.condition.details.sub_conditions),
                },
                "uri": self.condition.uri,
            },
            "amount": str(self.amount),
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
