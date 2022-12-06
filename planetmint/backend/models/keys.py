# Copyright © 2020 Interplanetary Database Association e.V.,
# Planetmint and IPDB software contributors.
# SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
# Code is Apache-2.0 and docs are CC-BY-4.0

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Keys:
    tx_id: str = ""
    output_id: str = ""
    public_keys: [str] = ""

    @staticmethod
    def from_dict(output: dict, tx_id: str = "") -> Keys:
        return Keys(
            tx_id=tx_id,
            public_keys=output["public_keys"],
        )

    @staticmethod
    def from_tuple(output: tuple) -> Keys:
        return Keys(
            tx_id=output[1],
            output_id=output[2],
            public_keys=output[3],
        )

    def to_dict(self) -> dict:
        return {
            "tx_id": self.tx_id,
            "output_id": self.output_id,
            "public_keys": self.public_keys,
        }
