

# Configuration Settings

Every Planetmint Server configuration setting has two names: a config-file name and an environment variable name. For example, one of the settings has the config-file name `database.host` and the environment variable name `PLANETMINT_DATABASE_HOST`. Here are some more examples:

`database.port` ↔ `PLANETMINT_DATABASE_PORT`

`database.keyfile_passphrase` ↔ `PLANETMINT_DATABASE_KEYFILE_PASSPHRASE`

`server.bind` ↔ `PLANETMINT_SERVER_BIND`

The value of each setting is determined according to the following rules:

* If it's set by an environment variable, then use that value
* Otherwise, if it's set in a local config file, then use that value
* Otherwise, use the default value

The local config file is `$HOME/.planetmint` by default (a file which might not even exist), but you can tell Planetmint to use a different file by using the `-c` command-line option, e.g. `planetmint -c path/to/config_file.json start`
or using the `PLANETMINT_CONFIG_PATH` environment variable, e.g. `PLANETMINT_CONFIG_PATH=.my_planetmint_config planetmint start`.
Note that the `-c` command line option will always take precedence if both the `PLANETMINT_CONFIG_PATH` and the `-c` command line option are used.

You can read the current default values in the file [planetmint/\_\_init\_\_.py](https://github.com/planetmint/planetmint/blob/master/planetmint/__init__.py). (The link is to the latest version.)


## database.*

The settings with names of the form `database.*` are for the backend database
(currently only Tarantool). They are:

* `database.backend` can only be `localtarantool`, currently.
* `database.host` is the hostname (FQDN) of the backend database.
* `database.port` is self-explanatory.
* `database.user` is a user-chosen name for the database inside Tarantool, e.g. `planetmint`.
* `database.pass` is the password of the user for connection to tarantool listener.

There are two ways for Planetmint Server to authenticate itself with Tarantool (or a specific Tarantool service): no authentication, username/password.

**No Authentication**

If you use all the default Planetmint configuration settings, then no authentication will be used.

**Username/Password Authentication**

To use username/password authentication, a Tarantool instance must already be running somewhere (maybe in another machine), it must already have a spaces for use by Planetmint, and that database must already have a "readWrite" user with associated username and password.

**Default values**

```js
"database": {
    "backend": "tarantool",
    "host": "localhost",
    "port": 3301,
    "username": null,
    "password": null
    
}
```

## server.*

`server.bind`, `server.loglevel` and `server.workers`
are settings for the [Gunicorn HTTP server](http://gunicorn.org/), which is used to serve the [HTTP client-server API](../connecting/http-client-server-api).

`server.bind` is where to bind the Gunicorn HTTP server socket. It's a string. It can be any valid value for [Gunicorn's bind setting](http://docs.gunicorn.org/en/stable/settings.html#bind). For example:

* If you want to allow IPv4 connections from anyone, on port 9984, use `0.0.0.0:9984`
* If you want to allow IPv6 connections from anyone, on port 9984, use `[::]:9984`

In a production setting, we recommend you use Gunicorn behind a reverse proxy server such as NGINX. If Gunicorn and the reverse proxy are running on the same machine, then you can use `localhost:9984` (the default value), meaning Gunicorn will talk to the reverse proxy on port 9984. The reverse proxy could then be bound to port 80 (for HTTP) or port 443 (for HTTPS), so that external clients would connect using that port. For example:

[External clients]---(port 443)---[NGINX]---(port 9984)---[Gunicorn / Planetmint Server]

If Gunicorn and the reverse proxy are running on different machines, then `server.bind` should be `hostname:9984`, where hostname is the IP address or [FQDN](https://en.wikipedia.org/wiki/Fully_qualified_domain_name) of the reverse proxy.

There's [more information about deploying behind a reverse proxy in the Gunicorn documentation](http://docs.gunicorn.org/en/stable/deploy.html). (They call it a proxy.)

`server.loglevel` sets the log level of Gunicorn's Error log outputs. See
[Gunicorn's documentation](http://docs.gunicorn.org/en/latest/settings.html#loglevel)
for more information.

`server.workers` is [the number of worker processes](http://docs.gunicorn.org/en/stable/settings.html#workers) for handling requests. If set to `None`, the value will be (2 × cpu_count + 1). Each worker process has a single thread. The HTTP server will be able to handle `server.workers` requests simultaneously.

**Example using environment variables**

```text
export PLANETMINT_SERVER_BIND=0.0.0.0:9984
export PLANETMINT_SERVER_LOGLEVEL=debug
export PLANETMINT_SERVER_WORKERS=5
```

**Example config file snippet**

```js
"server": {
    "bind": "0.0.0.0:9984",
    "loglevel": "debug",
    "workers": 5,
}
```

**Default values (from a config file)**

```js
"server": {
    "bind": "localhost:9984",
    "loglevel": "info",
    "workers": null,
}
```

## wsserver.*


### wsserver.scheme, wsserver.host and wsserver.port

These settings are for the
[aiohttp server](https://aiohttp.readthedocs.io/en/stable/index.html),
which is used to serve the
[WebSocket Event Stream API](../connecting/websocket-event-stream-api).
`wsserver.scheme` should be either `"ws"` or `"wss"`
(but setting it to `"wss"` does *not* enable SSL/TLS).
`wsserver.host` is where to bind the aiohttp server socket and
`wsserver.port` is the corresponding port.
If you want to allow connections from anyone, on port 9985,
set `wsserver.host` to 0.0.0.0 and `wsserver.port` to 9985.

**Example using environment variables**

```text
export PLANETMINT_WSSERVER_SCHEME=ws
export PLANETMINT_WSSERVER_HOST=0.0.0.0
export PLANETMINT_WSSERVER_PORT=9985
```

**Example config file snippet**

```js
"wsserver": {
    "scheme": "wss",
    "host": "0.0.0.0",
    "port": 65000
}
```

**Default values (from a config file)**

```js
"wsserver": {
    "scheme": "ws",
    "host": "localhost",
    "port": 9985
}
```

### wsserver.advertised_scheme, wsserver.advertised_host and wsserver.advertised_port

These settings are for the advertising the Websocket URL to external clients in
the root API endpoint. These configurations might be useful if your deployment
is hosted behind a firewall, NAT, etc. where the exposed public IP or domain is
different from where Planetmint is running.

**Example using environment variables**

```text
export PLANETMINT_WSSERVER_ADVERTISED_SCHEME=wss
export PLANETMINT_WSSERVER_ADVERTISED_HOST=myplanetmint.io
export PLANETMINT_WSSERVER_ADVERTISED_PORT=443
```

**Example config file snippet**

```js
"wsserver": {
    "advertised_scheme": "wss",
    "advertised_host": "myplanetmint.io",
    "advertised_port": 443
}
```

**Default values (from a config file)**

```js
"wsserver": {
    "advertised_scheme": "ws",
    "advertised_host": "localhost",
    "advertised_port": 9985
}
```

## log.*

The `log.*` settings are to configure logging.

**Example**

```js
{
    "log": {
        "file": "/var/log/planetmint.log",
        "error_file": "/var/log/planetmint-errors.log",
        "level_console": "info",
        "level_logfile": "info",
        "datefmt_console": "%Y-%m-%d %H:%M:%S",
        "datefmt_logfile": "%Y-%m-%d %H:%M:%S",
        "fmt_console": "%(asctime)s [%(levelname)s] (%(name)s) %(message)s",
        "fmt_logfile": "%(asctime)s [%(levelname)s] (%(name)s) %(message)s",
        "granular_levels": {}
}
```

**Default values**

```js
{
    "log": {
        "file": "~/planetmint.log",
        "error_file": "~/planetmint-errors.log",
        "level_console": "info",
        "level_logfile": "info",
        "datefmt_console": "%Y-%m-%d %H:%M:%S",
        "datefmt_logfile": "%Y-%m-%d %H:%M:%S",
        "fmt_logfile": "[%(asctime)s] [%(levelname)s] (%(name)s) %(message)s (%(processName)-10s - pid: %(process)d)",
        "fmt_console": "[%(asctime)s] [%(levelname)s] (%(name)s) %(message)s (%(processName)-10s - pid: %(process)d)",
        "granular_levels": {}
}
```

### log.file

The full path to the file where logs should be written.
The user running `planetmint` must have write access to the
specified path.

**Log rotation:** Log files have a size limit of about 200 MB
and will be rotated up to five times.
For example, if `log.file` is set to `"~/planetmint.log"`, then
logs would always be written to `planetmint.log`. Each time the file
`planetmint.log` reaches 200 MB it will be closed and renamed
`planetmint.log.1`. If `planetmint.log.1` and `planetmint.log.2` already exist they
would be renamed `planetmint.log.2` and `planetmint.log.3`. This pattern would be
applied up to `planetmint.log.5` after which `planetmint.log.5` would be
overwritten by `planetmint.log.4`, thus ending the rotation cycle of whatever
logs were in `planetmint.log.5`.

### log.error_file

Similar to `log.file` (see above), this is the
full path to the file where error logs should be written.

### log.level_console

The log level used to log to the console. Possible allowed values are the ones
defined by [Python](https://docs.python.org/3.9/library/logging.html#levels),
but case-insensitive for the sake of convenience:

```text
"critical", "error", "warning", "info", "debug", "notset"
```

### log.level_logfile

The log level used to log to the log file. Possible allowed values are the ones
defined by [Python](https://docs.python.org/3.9/library/logging.html#levels),
but case-insensitive for the sake of convenience:

```text
"critical", "error", "warning", "info", "debug", "notset"
```

### log.datefmt_console

The format string for the date/time portion of a message, when logged to the
console.

For more information on how to construct the format string please consult the
table under [Python's documentation of time.strftime(format[, t])](https://docs.python.org/3.9/library/time.html#time.strftime).

### log.datefmt_logfile

The format string for the date/time portion of a message, when logged to a log
 file.

For more information on how to construct the format string please consult the
table under [Python's documentation of time.strftime(format[, t])](https://docs.python.org/3.9/library/time.html#time.strftime).

### log.fmt_console

A string used to format the log messages when logged to the console.

For more information on possible formatting options please consult Python's
documentation on
[LogRecord attributes](https://docs.python.org/3.9/library/logging.html#logrecord-attributes).

### log.fmt_logfile

A string used to format the log messages when logged to a log file.

For more information on possible formatting options please consult Python's
documentation on
[LogRecord attributes](https://docs.python.org/3.9/library/logging.html#logrecord-attributes).

### log.granular_levels

Log levels for Planetmint's modules. This can be useful to control the log
level of specific parts of the application. As an example, if you wanted the
logging of the `core.py` module to be more verbose, you would set the
 configuration shown in the example below.

**Example**

```js
{
    "log": {
        "granular_levels": {
            "bichaindb.core": "debug"
        }
}
```

**Default value**

```js
{}
```

## tendermint.*

The settings with names of the form `tendermint.*` tell Planetmint Server
where it can connect to the node's Tendermint instance.

* `tendermint.host` is the hostname (FQDN)/IP address of the Tendermint instance.
* `tendermint.port` is self-explanatory.

**Example using environment variables**

```text
export PLANETMINT_TENDERMINT_HOST=tendermint
export PLANETMINT_TENDERMINT_PORT=26657
```Planetmint

**Default values**

```js
"tendermint": {
    "host": "localhost",
    "port": 26657
}
```
