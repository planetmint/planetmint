<!---
Copyright © 2020 Interplanetary Database Association e.V.,
Planetmint and IPDB software contributors.
SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
Code is Apache-2.0 and docs are CC-BY-4.0
--->

# Run a Planetmint network with Ansible

**NOT for Production Use**

You can use the following instructions to deploy a single or multi node
Planetmint network for dev/test using Ansible. Ansible will configure the Planetmint node(s).

Currently, this workflow is only supported for the following distributions:
- Ubuntu >= 16.04
- CentOS >= 7
- Fedora >= 24
- MacOSX

## Minimum Requirements
Minimum resource requirements for a single node Planetmint dev setup. **The more the better**:
- Memory >= 512MB
- VCPUs >= 1

## Clone the Planetmint repository
```text
$ git clone https://github.com/planetmint/planetmint.git
```

## Install dependencies
- [Ansible](http://docs.ansible.com/ansible/latest/intro_installation.html)

You can also install `ansible` and other dependencies, if any, using the `boostrap.sh` script
inside the Planetmint repository.
Navigate to `planetmint/pkg/scripts` and run the `bootstrap.sh` script to install the dependencies
for your OS. The script also checks if the OS you are running is compatible with the
supported versions.

**Note**: `bootstrap.sh` only supports Ubuntu >= 16.04, CentOS >= 7 and Fedora >=24 and MacOSX.

```text
$ cd planetmint/pkg/scripts/
$ bash bootstrap.sh --operation install
```

### Planetmint Setup Configuration(s)
#### Local Setup
You can run the Ansible playbook `planetmint-start.yml` on your local dev machine and set up the Planetmint node where
Planetmint can be run as a process or inside a Docker container(s) depending on your configuration.

Before, running the playbook locally, you need to update the `hosts` and `stack-config.yml` configuration, which will notify Ansible that we need to run the play locally.

##### Update Hosts
Navigate to `planetmint/pkg/configuration/hosts` inside the Planetmint repository.
```text
$ cd planetmint/pkg/configuration/hosts
```

Edit `all` configuration file:
```text
# Delete any existing configuration in this file and insert
# Hostname of dev machine
<HOSTNAME> ansible_connection=local
```
##### Update Configuration
Navigate to `planetmint/pkg/configuration/vars` inside the Planetmint repository.
```text
$ cd planetmint/pkg/configuration/vars/stack-config.yml
```

Edit `bdb-config.yml` configuration file as per your requirements, sample configuration file(s):
```text
---
stack_type: "docker" 
stack_size: "4"


OR

---
stack_type: "local"
stack_type: "1"
```

### Planetmint Setup
Now, You can safely run the `planetmint-start.yml` playbook and everything will be taken care of by `Ansible`. To run the playbook please navigate to the `planetmint/pkg/configuration` directory inside the Planetmint repository and run the `planetmint-start.yml` playbook.

```text
$ cd planetmint/pkg/configuration/

$ ansible-playbook planetmint-start.yml -i hosts/all --extra-vars "operation=start home_path=$(pwd)"
```

After successful execution of the playbook, you can verify that Planetmint docker(s)/process(es) is(are) running.

Verify Planetmint process(es):
```text
$ ps -ef | grep planetmint
```

OR

Verify Planetmint Docker(s):
```text
$ docker ps | grep planetmint
```

You can now send transactions and verify the functionality of your Planetmint node.
See the [Planetmint Python Driver documentation](https://docs.planetmint.com/projects/py-driver/en/latest/index.html)
for details on how to use it.

**Note**: The `bdb_root_url` can be be one of the following:
```text
# Planetmint is running as a process
bdb_root_url = http://<HOST-IP>:9984

OR

# Planetmint is running inside a docker container
bdb_root_url = http://<HOST-IP>:<DOCKER-PUBLISHED-PORT>
```

**Note**: Planetmint has [other drivers as well](http://docs.planetmint.com/projects/server/en/latest/drivers-clients/index.html).

### Experimental: Running Ansible a Remote Dev/Host
#### Remote Setup
You can also run the Ansible playbook `planetmint-start.yml` on remote machine(s) and set up the Planetmint node where
Planetmint can run as a process or inside a Docker container(s) depending on your configuration.

Before, running the playbook on a remote host, you need to update the `hosts` and `stack-config.yml` configuration, which will notify Ansible that we need to run the play on a remote host.

##### Update Remote Hosts
Navigate to `planetmint/pkg/configuration/hosts` inside the Planetmint repository.
```text
$ cd planetmint/pkg/configuration/hosts
```

Edit `all` configuration file:
```text
# Delete any existing configuration in this file and insert
<Remote_Host_IP/Hostname> ansible_ssh_user=<USERNAME> ansible_sudo_pass=<PASSWORD>
```

**Note**: You can add multiple hosts to the `all` configuration file. Non-root user with sudo enabled password is needed because ansible will run some tasks that require those permissions.

**Note**: You can also use other methods to get inside the remote machines instead of password based SSH. For other methods
please consult [Ansible Documentation](http://docs.ansible.com/ansible/latest/intro_getting_started.html).

##### Update Remote Configuration
Navigate to `planetmint/pkg/configuration/vars` inside the Planetmint repository.
```text
$ cd planetmint/pkg/configuration/vars/stack-config.yml
```

Edit `stack-config.yml` configuration file as per your requirements, sample configuration file(s):
```text
---
stack_type: "docker" 
stack_size: "4"


OR

---
stack_type: "local"
stack_type: "1"
```

After, the configuration of remote hosts, [run the Ansible playbook and verify your deployment](#planetmint-setup-ansible).
