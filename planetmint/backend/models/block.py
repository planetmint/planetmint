# Copyright © 2020 Interplanetary Database Association e.V.,
# Planetmint and IPDB software contributors.
# SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
# Code is Apache-2.0 and docs are CC-BY-4.0

from __future__ import annotations
import json
from dataclasses import dataclass, field


@dataclass
class Block:
    id: str = ""
    app_hash: str = ""
    height: int = 0
    transactions: list[str] = field(default_factory=list)

    @staticmethod
    def from_tuple(block_tuple: tuple) -> Block:
        return Block(block_tuple[0], block_tuple[1], block_tuple[2], block_tuple[3])

    def to_dict(self) -> dict:
        return {"app_hash": self.app_hash, "height": self.height, "transaction_ids": self.transactions}
