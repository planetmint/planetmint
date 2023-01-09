# Copyright © 2020 Interplanetary Database Association e.V.,
# Planetmint and IPDB software contributors.
# SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
# Code is Apache-2.0 and docs are CC-BY-4.0

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional


@dataclass
class Script:
    script: dict = None

    @staticmethod
    def from_dict(script_dict: dict) -> Script | None:
        if script_dict is None:
            return None
        return Script(script_dict["script"])

    def to_dict(self) -> dict:
        return {"script": self.script}
