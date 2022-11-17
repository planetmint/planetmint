# Copyright © 2020 Interplanetary Database Association e.V.,
# Planetmint and IPDB software contributors.
# SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
# Code is Apache-2.0 and docs are CC-BY-4.0

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional

@dataclass
class Script:
    id: str = ""
    script: Optional[str] = None
    
    @staticmethod
    def from_tuple(script_tuple: tuple) -> Script:
        return Script(script_tuple[0], script_tuple[1])
    
    
