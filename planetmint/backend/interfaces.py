# Copyright © 2020 Interplanetary Database Association e.V.,
# Planetmint and IPDB software contributors.
# SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
# Code is Apache-2.0 and docs are CC-BY-4.0

from dataclasses import dataclass
from typing import Union

# Asset should represent a single asset (e.g.: tarantool tuple (data, tx_id, asset_id))
# If multiple assets are stored at once this should remain the same. 
# For Create ({'data': 'values'}, c_tx_id, c_tx_id), For Transfer ({'id': c_tx_id}, tx_id, c_tx_id)

@dataclass
class Asset:
    id: str = ""
    tx_id: str = ""
    data: str = ""

@dataclass
class MetaData:
    id: str = ""
    metadata: str = ""

@dataclass
class Input:
    tx_id: str = ""
    fulfills: Union[dict, None] = None
    owners_before: list[str] = None
    fulfillment: str = ""
    
@dataclass
class Output:
    id: str = None

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
    version: str = None # TODO: make enum
    operation: str = None # TODO: make enum
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

