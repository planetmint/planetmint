# Troubleshooting

## General Tips

- Check the Planetmint, Tendermint and Tarantool logs.
  For help with that, see the page about [Logging and Log Rotation](../appendices/log-rotation).
- Try Googling the error message.

## Tendermint Tips

* [Configure Tendermint to create no empty blocks](https://tendermint.io/docs/tendermint-core/using-tendermint.html#no-empty-blocks).
* Store the Tendermint data on a fast drive. You can do that by changing [the location of TMHOME](https://tendermint.io/docs/tendermint-core/using-tendermint.html#directory-root) to be on the fast drive.

See the [Tendermint tips in the vrde/notes repository](https://github.com/vrde/notes/tree/master/tendermint).

## Resolving Tendermint Connectivity Problems

To check which nodes your node is connected to (via Tendermint protocols), do:

```text
# if you don't have jq installed, then install it
sudo apt install jq
# then do
curl -s localhost:26657/net_info | jq ".result.peers[].node_info | {id, listen_addr, moniker}"
```

Note: Tendermint has other endpoints besides `/net_info`: see [the Tendermint RPC docs](https://tendermint.github.io/slate/?shell#introduction).

If you're running your network inside a [private network](https://en.wikipedia.org/wiki/Private_network), e.g. with IP addresses of the form 192.168.x.y, then you may have to change the following setting in `config.toml`:

```text
addr_book_strict = false
```

## Refreshing Your Node

If you want to refresh your node back to a fresh empty state, then your best bet is to terminate it and deploy a new machine, but if that's not an option, then you can:

* drop the `planetmint` database in tarantool using `planetmint drop` (but that only works if tarantool is running)
* reset Tendermint using `tendermint unsafe_reset_all`
* delete the directory `$HOME/.tendermint`

## Shutting Down Planetmint

If you want to stop/kill Planetmint, you can do so by sending `SIGINT`, `SIGQUIT` or `SIGTERM` to the running Planetmint
process(es). Depending on how you started Planetmint i.e. foreground or background. e.g. you started Planetmint in the background as mentioned above in the guide:

```bash
$ nohup planetmint start 2>&1 > planetmint.log &

$ # Check the PID of the main Planetmint process
$ ps -ef | grep planetmint
<user>    *<pid> <ppid>   <C> <STIME> <tty>        <time> planetmint
<user>     <pid> <ppid>*  <C> <STIME> <tty>        <time> gunicorn: master [planetmint_gunicorn]
<user>     <pid> <ppid>*  <C> <STIME> <tty>        <time> planetmint_ws
<user>     <pid> <ppid>*  <C> <STIME> <tty>        <time> planetmint_ws_to_tendermint
<user>     <pid> <ppid>*  <C> <STIME> <tty>        <time> planetmint_exchange
<user>     <pid> <ppid>   <C> <STIME> <tty>        <time> gunicorn: worker [planetmint_gunicorn]
<user>     <pid> <ppid>   <C> <STIME> <tty>        <time> gunicorn: worker [planetmint_gunicorn]
<user>     <pid> <ppid>   <C> <STIME> <tty>        <time> gunicorn: worker [planetmint_gunicorn]
<user>     <pid> <ppid>   <C> <STIME> <tty>        <time> gunicorn: worker [planetmint_gunicorn]
<user>     <pid> <ppid>   <C> <STIME> <tty>        <time> gunicorn: worker [planetmint_gunicorn]
...

$ # Send any of the above mentioned signals to the parent/root process(marked with `*` for clarity)
# Sending SIGINT
$ kill -2 <planetmint_parent_pid>

$ # OR

# Sending SIGTERM
$ kill -15 <planetmint_parent_pid>

$ # OR

# Sending SIGQUIT
$ kill -3 <planetmint_parent_pid>

# If you want to kill all the processes by name yourself
$ pgrep planetmint | xargs kill -9
```

If you started Planetmint in the foreground, a `Ctrl + C` or `Ctrl + Z` would shut down Planetmint.

## Member: Dynamically Add or Remove Validators

One member can make a proposal to call an election to add a validator, remove a validator, or change the voting power of a validator. They then share the election/proposal ID with all the other members. Once more than 2/3 of the voting power votes yes, the proposed change comes into effect. The commands to create a new election/proposal, to approve an election/proposal, and to get the current status of an election/proposal can be found in the documentation about the [planetmint election](tools/planetmint-cli#planetmint-election) subcommands.

## Logging

See the page in the Appendices about [logging and log rotation](../appendices/log-rotation).

## Other Problems

If you're stuck, maybe [file a new issue on GitHub](https://github.com/planetmint/planetmint/issues/new). If your problem occurs often enough, we'll write about it here.