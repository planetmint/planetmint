

# Set Up Planetmint, Tarantool and Tendermint

We now install and configure software that must run
in every Planetmint node: Planetmint Server,
Tarantool and Tendermint.

## Install Planetmint Server

Planetmint Server requires **Python 3.9+**, so make sure your system has it.

Install the required OS-level packages:

```
# For Ubuntu 18.04:
sudo apt install -y python3-pip libssl-dev
# Ubuntu 16.04, and other Linux distros, may require other packages or more packages
```

Planetmint Server requires [gevent](http://www.gevent.org/), and to install gevent, you must use pip 19 or later (as of 2019, because gevent now uses manylinux2010 wheels). Upgrade pip to the latest version:

```
sudo pip3 install -U pip
```

Now install the latest version of Planetmint Server.
You can find the latest version by going
to the [Planetmint project release history page on PyPI](https://pypi.org/project/Planetmint/#history).
For example, to install version 2.2.2, you would do:

```
# Change 2.0.0 to the latest version as explained above:
sudo pip3 install planetmint==2.2.2
```

Check that you installed the correct version of Planetmint Server using `planetmint --version`.

## Configure Planetmint Server

To configure Planetmint Server, run:

```
planetmint configure
```

The first question is ``API Server bind? (default `localhost:9984`)``.

* If you're using NGINX (e.g. if you want HTTPS),
  then accept the default value (`localhost:9984`).
* If you're not using NGINX, then enter the value `0.0.0.0:9984`

You can accept the default value for all other Planetmint config settings.

If you're using NGINX, then you should edit your Planetmint config file
(in `$HOME/.planetmint` by default) and set the following values
under `"wsserver"`:

```
"advertised_scheme": "wss",
"advertised_host": "bnode.example.com",
"advertised_port": 443
```

where `bnode.example.com` should be replaced by your node's actual subdomain.

## Install (and Start) Tarantool

Install a recent version of Tarantool.
Planetmint Server requires version 3.4 or newer.

```
curl -L https://tarantool.io/DDJLJzv/release/2.8/installer.sh | bash

sudo apt-get -y install tarantool
```

## Sharding with Tarantool

If the load on a single node becomes to large Tarantool allows for sharding to scale horizontally.
For more information on how to setup sharding with Tarantool please refer to the [official Tarantool documentation](https://www.tarantool.io/en/doc/latest/reference/reference_rock/vshard/vshard_index/).

## Install Tendermint

The version of Planetmint Server described in these docs only works well
with Tendermint 0.31.5 (not a higher version number). Install that:

```
sudo apt install -y unzip
wget https://github.com/tendermint/tendermint/releases/download/v0.31.5/tendermint_v0.31.5_linux_amd64.zip
unzip tendermint_v0.31.5_linux_amd64.zip
rm tendermint_v0.31.5_linux_amd64.zip
sudo mv tendermint /usr/local/bin
```

## Start Configuring Tendermint

You won't be able to finish configuring Tendermint until you have some information
from the other nodes in the network, but you can start by doing:

```
tendermint init
```
