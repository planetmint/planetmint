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
    metadata: MetaData = None
    assets: list[Asset] = None
    inputs: list[Input] = None
    script: Script = None

    @staticmethod
    def from_dict(transaction: dict) -> DbTransaction:
        return DbTransaction(
            id=transaction["id"],
            operation=transaction["operation"],
            version=transaction["version"],
            inputs=Input.from_list_dict(transaction["inputs"]),
            assets=Asset.from_list_dict(transaction["assets"]),
            metadata=MetaData.from_dict(transaction["metadata"]),
            script=Script.from_dict(transaction["script"]),
        )

    @staticmethod
    def from_tuple(transaction: tuple) -> DbTransaction:
        return DbTransaction(
            id=transaction[0],
            operation=transaction[1],
            version=transaction[2],
            metadata=MetaData.from_dict(transaction[3]),
            assets=Asset.from_list_dict(transaction[4]),
            inputs=Input.from_list_dict(transaction[5]),
            script=Script.from_dict(transaction[6]),
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "operation": self.operation,
            "version": self.version,
            "inputs": Input.list_to_dict(self.inputs),
            "assets": Asset.list_to_dict(self.assets),
            "metadata": self.metadata.to_dict() if self.metadata is not None else None,
            "script": self.script.to_dict() if self.script is not None else None,
        }
