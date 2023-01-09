# Copyright © 2020 Interplanetary Database Association e.V.,
# Planetmint and IPDB software contributors.
# SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
# Code is Apache-2.0 and docs are CC-BY-4.0

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional

from .fulfills import Fulfills


@dataclass
class Input:
    tx_id: str = ""
    fulfills: Optional[Fulfills] = None
    owners_before: list[str] = field(default_factory=list)
    fulfillment: str = ""

    @staticmethod
    def from_dict(input_dict: dict, tx_id: str = "") -> Input:
        fulfills = None

        if input_dict["fulfills"]:
            fulfills = Fulfills(input_dict["fulfills"]["transaction_id"], input_dict["fulfills"]["output_index"])

        return Input(tx_id, fulfills, input_dict["owners_before"], input_dict["fulfillment"])

    @staticmethod
    def from_tuple(input_tuple: tuple) -> Input:
        tx_id = input_tuple[0]
        fulfillment = input_tuple[1]
        owners_before = input_tuple[2]
        fulfills = None
        fulfills_tx_id = input_tuple[3]

        if fulfills_tx_id:
            # TODO: the output_index should be an unsigned int
            fulfills = Fulfills(fulfills_tx_id, int(input_tuple[4]))

        return Input(tx_id, fulfills, owners_before, fulfillment)

    def to_dict(self) -> dict:
        fulfills = (
            {"transaction_id": self.fulfills.transaction_id, "output_index": self.fulfills.output_index}
            if self.fulfills
            else None
        )

        return {"owners_before": self.owners_before, "fulfills": fulfills, "fulfillment": self.fulfillment}

    @staticmethod
    def from_list_dict(input_tuple_list: list[dict]) -> list[Input]:
        return [Input.from_dict(input_tuple) for input_tuple in input_tuple_list]

    @staticmethod
    def list_to_dict(input_list: list[Input]) -> list[dict]:
        return [input.to_dict() for input in input_list or []]
