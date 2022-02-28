#!/bin/bash
# Copyright © 2020 Interplanetary Database Association e.V.,
# Planetmint and IPDB software contributors.
# SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
# Code is Apache-2.0 and docs are CC-BY-4.0

result=$(ssh -o "StrictHostKeyChecking=no" -i \~/.ssh/id_rsa root@planetmint_1 'bash -s' < scripts/election.sh elect 2)
ssh -o "StrictHostKeyChecking=no" -i ~/.ssh/id_rsa root@planetmint_2 'bash -s' < scripts/election.sh approve $result

exec "$@"