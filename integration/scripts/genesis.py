#!/usr/bin/env python3
# Copyright © 2020 Interplanetary Database Association e.V.,
# Planetmint and IPDB software contributors.
# SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
# Code is Apache-2.0 and docs are CC-BY-4.0

import json
import sys


def edit_genesis() -> None:
    file_names = sys.argv[1:]

    validators = []
    for file_name in file_names:
        file = open(file_name)
        genesis = json.load(file)
        validators.extend(genesis["validators"])
        file.close()

    genesis_file = open(file_names[0])
    genesis_json = json.load(genesis_file)
    genesis_json["validators"] = validators
    genesis_file.close()

    with open("/shared/genesis.json", "w") as f:
        json.dump(genesis_json, f, indent=True)

    return None


if __name__ == "__main__":
    edit_genesis()
