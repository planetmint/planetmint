# Copyright © 2020 Interplanetary Database Association e.V.,
# Planetmint and IPDB software contributors.
# SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
# Code is Apache-2.0 and docs are CC-BY-4.0

from __future__ import annotations
from dataclasses import dataclass


@dataclass
class Asset:
    key: str = ""
    data: str = ""

    @staticmethod
    def from_dict(asset_dict: dict) -> Asset:
        key = "data" if "data" in asset_dict.keys() else "id"
        data = asset_dict[key]
        return Asset(key, data)

    def to_dict(self) -> dict:
        return {self.key: self.data}

    @staticmethod
    def from_list_dict(asset_dict_list: list[dict]) -> list[Asset]:
        return [Asset.from_dict(asset_dict) for asset_dict in asset_dict_list if isinstance(asset_dict, dict)]

    @staticmethod
    def list_to_dict(asset_list: list[Asset]) -> list[dict]:
        return [asset.to_dict() for asset in asset_list or []]
