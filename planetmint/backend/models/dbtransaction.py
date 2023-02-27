# Copyright © 2020 Interplanetary Database Association e.V.,
# Planetmint and IPDB software contributors.
# SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
# Code is Apache-2.0 and docs are CC-BY-4.0

from __future__ import annotations
from dataclasses import dataclass, field

from planetmint.backend.models import Asset, MetaData, Input, Script, Output


@dataclass
class DbTransaction:
    id: str = ""
    operation: str = ""
    version: str = ""
    metadata: MetaData = None
    assets: list[Asset] = field(default_factory=list)
    inputs: list[Input] = field(default_factory=list)
    outputs: list[Output] = field(default_factory=list)
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
            script=Script.from_dict(transaction["script"]) if "script" in transaction else None,
        )

    @staticmethod
    def from_tuple(transaction: tuple) -> DbTransaction:
        assets = Asset.from_list_dict(transaction[4])
        return DbTransaction(
            id=transaction[0],
            operation=transaction[1],
            version=transaction[2],
            metadata=MetaData.from_dict(transaction[3]),
            assets=assets if transaction[2] != "2.0" else [assets[0]],
            inputs=Input.from_list_dict(transaction[5]),
            script=Script.from_dict(transaction[6]),
        )

    @staticmethod
    def remove_generated_fields(tx_dict: dict) -> dict:
        tx_dict["outputs"] = [
            DbTransaction.remove_generated_or_none_output_keys(output) for output in tx_dict["outputs"]
        ]
        if "script" in tx_dict and tx_dict["script"] is None:
            tx_dict.pop("script")
        return tx_dict

    @staticmethod
    def remove_generated_or_none_output_keys(output: dict) -> dict:
        output["condition"]["details"] = {k: v for k, v in output["condition"]["details"].items() if v is not None}
        if "id" in output:
            output.pop("id")
        return output

    def to_dict(self) -> dict:
        """

        Returns
        -------
        object
        """
        assets = Asset.list_to_dict(self.assets)
        tx = {
            "inputs": Input.list_to_dict(self.inputs),
            "outputs": Output.list_to_dict(self.outputs),
            "operation": self.operation,
            "metadata": self.metadata.to_dict() if self.metadata is not None else None,
            "assets": assets if self.version != "2.0" else assets[0],
            "version": self.version,
            "id": self.id,
            "script": self.script.to_dict() if self.script is not None else None,
        }
        tx = DbTransaction.remove_generated_fields(tx)
        return tx
