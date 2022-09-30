

# Production Node Components

A production Planetmint node must include:

* Planetmint Server
* Tarantool
* Tendermint
* Storage for MongoDB and Tendermint

It could also include several other components, including:

* NGINX or similar, to provide authentication, rate limiting, etc.
* An NTP daemon running on all machines running Planetmint Server or tarantool, and possibly other machines

* Log aggregation software
* Monitoring software
* Maybe more

The relationship between the main components is illustrated below.

![Components of a production node](../../_static/Node-components.png)
