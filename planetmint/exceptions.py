# Copyright © 2020 Interplanetary Database Association e.V.,
# Planetmint and IPDB software contributors.
# SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
# Code is Apache-2.0 and docs are CC-BY-4.0


class PlanetmintError(Exception):
    """Base class for Planetmint exceptions."""


class CriticalDoubleSpend(PlanetmintError):
    """Data integrity error that requires attention"""
