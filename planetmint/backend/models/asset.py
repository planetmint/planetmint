# Copyright © 2020 Interplanetary Database Association e.V.,
# Planetmint and IPDB software contributors.
# SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
# Code is Apache-2.0 and docs are CC-BY-4.0

from __future__ import annotations
import json
from dataclasses import dataclass


@dataclass
class Asset:
    data: str = ""

    @staticmethod
    def from_dict(asset_tuple: dict) -> Asset:
        return Asset(asset_tuple["data"])

    def to_dict(self) -> dict:
        return {
            "data": self.data
        }

    @staticmethod
    def from_list_dict(asset_tuple_list: list[tuple]) -> list[Asset]:
        return [Asset.from_dict(asset_tuple) for asset_tuple in asset_tuple_list]

    @staticmethod
    def list_to_dict(asset_list: list[Asset]) -> list[dict]:
        return [asset.to_dict() for asset in asset_list or []]
