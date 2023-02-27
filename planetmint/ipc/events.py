# Copyright © 2020 Interplanetary Database Association e.V.,
# Planetmint and IPDB software contributors.
# SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
# Code is Apache-2.0 and docs are CC-BY-4.0

POISON_PILL = "POISON_PILL"


class EventTypes:
    """Container class that holds all the possible
    events Planetmint manages.
    """

    # If you add a new Event Type, make sure to add it
    # to the docs in docs/server/source/event-plugin-api.rst
    ALL = ~0
    BLOCK_VALID = 1
    BLOCK_INVALID = 2
    # NEW_EVENT = 4
    # NEW_EVENT = 8
    # NEW_EVENT = 16...


class Event:
    """An Event."""

    def __init__(self, event_type, event_data):
        """Creates a new event.

        Args:
            event_type (int): the type of the event, see
                :class:`~planetmint.events.EventTypes`
            event_data (obj): the data of the event.
        """

        self.type = event_type
        self.data = event_data
