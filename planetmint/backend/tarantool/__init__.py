# Register the single dispatched modules on import.
from planetmint.backend.tarantool import query, connection, schema  # noqa

# MongoDBConnection should always be accessed via
# ``planetmint.backend.connect()``.
