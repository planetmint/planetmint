# Copyright © 2020 Interplanetary Database Association e.V.,
# Planetmint and IPDB software contributors.
# SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
# Code is Apache-2.0 and docs are CC-BY-4.0

import subprocess
import pytest


@pytest.mark.skip
def test_build_root_docs():
    proc = subprocess.Popen(["bash"], stdin=subprocess.PIPE)
    proc.stdin.write("cd docs/root; make html".encode())
    proc.stdin.close()
    assert proc.wait() == 0
