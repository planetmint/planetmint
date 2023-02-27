from queue import Empty
from collections import defaultdict
import multiprocessing

from planetmint.ipc.events import EventTypes, POISON_PILL


class Exchange:
    """Dispatch events to subscribers."""

    def __init__(self):
        self.publisher_queue = multiprocessing.Queue()
        self.started_queue = multiprocessing.Queue()

        # Map <event_types -> queues>
        self.queues = defaultdict(list)

    def get_publisher_queue(self):
        """Get the queue used by the publisher.

        Returns:
            a :class:`multiprocessing.Queue`.
        """

        return self.publisher_queue

    def get_subscriber_queue(self, event_types=None):
        """Create a new queue for a specific combination of event types
        and return it.

        Returns:
            a :class:`multiprocessing.Queue`.
        Raises:
            RuntimeError if called after `run`
        """

        try:
            self.started_queue.get(timeout=1)
            raise RuntimeError("Cannot create a new subscriber queue while Exchange is running.")
        except Empty:
            pass

        if event_types is None:
            event_types = EventTypes.ALL

        queue = multiprocessing.Queue()
        self.queues[event_types].append(queue)
        return queue

    def dispatch(self, event):
        """Given an event, send it to all the subscribers.

        Args
            event (:class:`~planetmint.events.EventTypes`): the event to
                dispatch to all the subscribers.
        """

        for event_types, queues in self.queues.items():
            if event.type & event_types:
                for queue in queues:
                    queue.put(event)

    def run(self):
        """Start the exchange"""
        self.started_queue.put("STARTED")

        while True:
            event = self.publisher_queue.get()
            if event == POISON_PILL:
                return
            else:
                self.dispatch(event)
