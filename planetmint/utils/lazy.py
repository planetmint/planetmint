class Lazy:
    """Lazy objects are useful to create chains of methods to
    execute later.

    A lazy object records the methods that has been called, and
    replay them when the :py:meth:`run` method is called. Note that
    :py:meth:`run` needs an object `instance` to replay all the
    methods that have been recorded.
    """

    def __init__(self):
        """Instantiate a new Lazy object."""
        self.stack = []

    def __getattr__(self, name):
        self.stack.append(name)
        return self

    def __call__(self, *args, **kwargs):
        self.stack.append((args, kwargs))
        return self

    def __getitem__(self, key):
        self.stack.append("__getitem__")
        self.stack.append(([key], {}))
        return self

    def run(self, instance):
        """Run the recorded chain of methods on `instance`.

        Args:
            instance: an object.
        """

        last = instance

        for item in self.stack:
            if isinstance(item, str):
                last = getattr(last, item)
            else:
                last = last(*item[0], **item[1])

        self.stack = []
        return last
