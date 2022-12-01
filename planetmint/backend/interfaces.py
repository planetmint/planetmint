# Copyright © 2020 Interplanetary Database Association e.V.,
# Planetmint and IPDB software contributors.
# SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
# Code is Apache-2.0 and docs are CC-BY-4.0

from dataclasses import dataclass

# NOTE: only here temporarily
from planetmint.backend.models import Asset, MetaData, Input
from planetmint.backend.models import Output


@dataclass
class Block:
    id: str = None
    app_hash: str = None
    height: int = None


@dataclass
class Script:
    id: str = None
    script = None


@dataclass
class UTXO:
    id: str = None
    output_index: int = None
    utxo: dict = None


@dataclass
class Transaction:
    id: str = None
    assets: list[Asset] = None
    metadata: MetaData = None
    version: str = None  # TODO: make enum
    operation: str = None  # TODO: make enum
    inputs: list[Input] = None
    outputs: list[Output] = None
    script: str = None


@dataclass
class Validator:
    id: str = None
    height: int = None
    validators = None


@dataclass
class ABCIChain:
    height: str = None
    is_synced: bool = None
    chain_id: str = None
