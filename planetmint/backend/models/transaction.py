# Copyright © 2020 Interplanetary Database Association e.V.,
# Planetmint and IPDB software contributors.
# SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
# Code is Apache-2.0 and docs are CC-BY-4.0

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional

@dataclass
class Transaction:
    id: str = ""
    operation: str = ""
    version: str = ""
    raw_transaction: dict = dict

    @staticmethod
    def from_dict(transaction: dict) -> Transaction:
        return Transaction(
            id=transaction["id"],
            operation=transaction["operation"],
            version=transaction["version"],
            raw_transaction=transaction["transaction"],
        )


    @staticmethod
    def from_tuple(transaction: tuple) -> Transaction:
        return Transaction(
            id=transaction[0],
            operation=transaction[1],
            version=transaction[2],
            raw_transaction=transaction[3],
        )


    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "operation": self.operation,
            "version": self.version,
            "transaction": self.raw_transaction,
        }
