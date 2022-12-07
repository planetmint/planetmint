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
    metadata: Optional[str] = None

    @staticmethod
    def from_dict(meta_data_tuple: dict) -> MetaData:
        if meta_data_tuple is None:
            return MetaData()
        return MetaData(meta_data_tuple["meta_data"])

    def to_dict(self) -> dict:
        return {
            "metadata": self.metadata
        }
