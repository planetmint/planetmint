# Copyright © 2020 Interplanetary Database Association e.V.,
# Planetmint and IPDB software contributors.
# SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
# Code is Apache-2.0 and docs are CC-BY-4.0

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List


@dataclass
class ConditionDetails:
    type: str = ""
    public_key: str = ""
    threshold: int = None
    sub_conditions: List[ConditionDetails] = field(default_factory=list)

    def to_dict(self) -> dict:
        if self.sub_conditions is None:
            return {"type": self.type, "public_key": self.public_key}
        else:
            return {
                "type": self.type,
                "threshold": self.threshold,
                "subconditions": [sub_condition.to_dict() for sub_condition in self.sub_conditions],
            }

    @staticmethod
    def from_dict(details: dict) -> ConditionDetails:
        sub_conditions = None
        if "subconditions" in details:
            sub_conditions = [ConditionDetails.from_dict(sub_condition) for sub_condition in details["subconditions"]]
        return ConditionDetails(
            type=details.get("type"),
            public_key=details.get("public_key"),
            threshold=details.get("threshold"),
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
            out_dict = Output.output_with_public_key(output, transaction_id)
        else:
            out_dict = Output.output_with_sub_conditions(output, transaction_id)
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
            # "id": self.id,
            "public_keys": self.public_keys,
            "condition": self.condition.to_dict(),
            "amount": str(self.amount),
        }

    @staticmethod
    def list_to_dict(output_list: list[Output]) -> list[dict]:
        return [output.to_dict() for output in output_list or []]

    @staticmethod
    def output_with_public_key(output, transaction_id) -> Output:
        return Output(
            transaction_id=transaction_id,
            public_keys=output["public_keys"],
            amount=output["amount"],
            condition=Condition(
                uri=output["condition"]["uri"], details=ConditionDetails.from_dict(output["condition"]["details"])
            ),
        )

    @staticmethod
    def output_with_sub_conditions(output, transaction_id) -> Output:
        return Output(
            transaction_id=transaction_id,
            public_keys=output["public_keys"],
            amount=output["amount"],
            condition=Condition(
                uri=output["condition"]["uri"], details=ConditionDetails.from_dict(output["condition"]["details"])
            ),
        )
