# Copyright © 2020 Interplanetary Database Association e.V.,
# Planetmint and IPDB software contributors.
# SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
# Code is Apache-2.0 and docs are CC-BY-4.0

from dataclasses import dataclass, field
from typing import Optional

from .fulfills import Fulfills

@dataclass
class Input:
    tx_id: str = ""
    fulfills: Optional[Fulfills] = None
    owners_before: list[str] = field(default_factory=list)
    fulfillment: str = ""