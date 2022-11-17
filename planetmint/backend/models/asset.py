# Copyright © 2020 Interplanetary Database Association e.V.,
# Planetmint and IPDB software contributors.
# SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
# Code is Apache-2.0 and docs are CC-BY-4.0

from __future__ import annotations
import json
from dataclasses import dataclass

@dataclass
class Asset:
    id: str = ""
    tx_id: str = ""
    data: str = ""
    
    @staticmethod
    def from_tuple(asset_tuple: tuple) -> Asset:
        return Asset(asset_tuple[2], asset_tuple[1], json.loads(asset_tuple[0]))