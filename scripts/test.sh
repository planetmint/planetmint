#!/bin/bash
# Copyright © 2020 Interplanetary Database Association e.V.,
# Planetmint and IPDB software contributors.
# SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
# Code is Apache-2.0 and docs are CC-BY-4.0

result=$(ssh -o StrictHostKeyChecking=accept-new root@64.225.106.52 -i id_ed25519 'bash -s' < scripts/election.sh elect 35)
ssh -o StrictHostKeyChecking=accept-new root@64.225.105.60 -i id_ed25519 'bash -s' < scripts/election.sh approve $result