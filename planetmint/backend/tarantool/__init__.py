# Register the single dispatched modules on import.
from planetmint.backend.tarantool import schema, query, connection # noqa

# MongoDBConnection should always be accessed via
# ``planetmint.backend.connect()``.