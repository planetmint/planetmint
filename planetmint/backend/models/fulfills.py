# Copyright © 2020 Interplanetary Database Association e.V.,
# Planetmint and IPDB software contributors.
# SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
# Code is Apache-2.0 and docs are CC-BY-4.0

from dataclasses import dataclass


@dataclass
class Fulfills:
    transaction_id: str = ""
    output_index: int = 0

    def to_dict(self) -> dict:
        return {"transaction_id": self.transaction_id, "output_index": self.output_index}
