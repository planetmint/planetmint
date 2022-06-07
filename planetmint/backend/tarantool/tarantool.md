# How to start using planetmint with tarantool

First of all you have do download [Tarantool](https://www.tarantool.io/en/download/os-installation/ubuntu/).


## How to connect tarantool to planetmint

After a successful instalation you should be able to run from you terminal command ```tarantool```. In the cli of tarantool you need initializa a listening following the example :
```
box.cfg{listen=3301}
```
[^1].
Afterwards quit cli of tarantool and scan by port if to be sure that service was created by tarantool.

### How to init spaces and indexes of tarantool[^2].

For this step you need to go in the root folder of planetmint and run from your virtual enviroment:

```
python planetmint init localhost 3301 admin pass
```

### In case you want to reset tarantool you can run command above and adding at the end True.


[^1]: This is example of the port address that can be used.

[^2]: Not yet working



