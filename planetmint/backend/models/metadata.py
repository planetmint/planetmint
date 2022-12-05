# Copyright © 2020 Interplanetary Database Association e.V.,
# Planetmint and IPDB software contributors.
# SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
# Code is Apache-2.0 and docs are CC-BY-4.0

from __future__ import annotations
import json
from dataclasses import dataclass
from typing import Optional


@dataclass
class MetaData:
    id: str = ""
    metadata: Optional[str] = None

    @staticmethod
    def from_tuple(meta_data_tuple: tuple) -> MetaData:
        return MetaData(meta_data_tuple[0], json.loads(meta_data_tuple[1]))

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "metadata": self.metadata
        }
