

# Production Node Requirements

**This page is about the requirements of Planetmint Server.** You can find the requirements of Tarantool, Tendermint and other [production node components](node-components) in the documentation for that software.

## OS Requirements

Planetmint Server requires Python 3.9+ and Python 3.9+ [will run on any modern OS](https://docs.python.org/3.5/using/index.html), but we recommend using an LTS version of [Ubuntu Server](https://www.ubuntu.com/server) or a similarly server-grade Linux distribution.

_Don't use macOS_ (formerly OS X, formerly Mac OS X), because it's not a server-grade operating system. Also, Planetmint Server uses the Python multiprocessing package and [some functionality in the multiprocessing package doesn't work on Mac OS X](https://docs.python.org/3.9/library/multiprocessing.html#multiprocessing.Queue.qsize).

## General Considerations

Planetmint Server runs many concurrent processes, so more RAM and more CPU cores is better.

As mentioned on the page about [production node components](node-components), every machine running Planetmint Server should be running an NTP daemon.
