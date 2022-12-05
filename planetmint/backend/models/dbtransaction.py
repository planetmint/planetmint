# Copyright © 2020 Interplanetary Database Association e.V.,
# Planetmint and IPDB software contributors.
# SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
# Code is Apache-2.0 and docs are CC-BY-4.0

from __future__ import annotations
from dataclasses import dataclass

from planetmint.backend.models import Asset, MetaData, Input, Output, Script
from planetmint.backend.models.keys import Keys


@dataclass
class DbTransaction:
    id: str = ""
    operation: str = ""
    version: str = ""
    raw_transaction: dict = dict
    assets: list[Asset] = None
    metadata: MetaData = None
    inputs: list[Input] = None
    outputs: list[Output] = None
    keys: Keys = None
    script: Script = None

    @staticmethod
    def from_dict(transaction: dict) -> DbTransaction:
        return DbTransaction(
            id=transaction["id"],
            operation=transaction["operation"],
            version=transaction["version"],
            inputs=transaction["inputs"],
            raw_transaction=transaction["transaction"],
        )

    @staticmethod
    def from_tuple(transaction: tuple) -> DbTransaction:
        return DbTransaction(
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
            "inputs": Input.list_to_dict(self.inputs),
            "assets": Asset.list_to_dict(self.assets),
            "metadata": self.metadata.to_dict(),
            "outputs": Output.list_to_dict(self.outputs),
            "keys": self.keys.to_dict(),
            "script": self.script.to_dict(),
            "transaction": self.raw_transaction,
        }
