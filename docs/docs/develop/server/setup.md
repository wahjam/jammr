A local development environment consists of two items:

1. A git checkout of the server source code. Code can be edited locally with
   any Integrated Development Environment (IDE) or text editor. Container
   images are also built locally using Docker.
1. At least one virtual machine or external server where the containers will be
   deployed. Creating a virtual machine on the local machine is recommended.

Developing locally with a virtual machine
-----------------------------------------
To set up a development environment using libvirt on a Linux host, create a new
virtual machine called 'dev1.jammr.net' running Debian stable:

```
virt-install --name dev1.jammr.net --memory 1024 --cpu host \
    --location https://ftp.debian.org/debian/dists/buster/main/installer-amd64/ \
    --os-variant=debian10 \
    --disk size=20,cache=none
```

Set the hostname to 'dev1.jammr.net' and ensure that openssh-server will be
installed. Complete the installation and start the virtual machine.

Add your ssh key to access root@dev1.jammr.net:

```
(dev1.jammr.net)# mkdir .ssh
(dev1.jammr.net)# cat >.ssh/authorized_keys
...your ssh public key here...
^D
(dev1.jammr.net)# chmod 700 .ssh && chmod 600 .ssh/authorized_keys
```

Set up Ansible in a virtual environment. Installing a specific Ansible version
ensures that updates to the system Ansible (if it's installed) don't break the
playbooks:

```
(local)$ python -m venv .
(local)$ bin/pip install ansible==5.9.0 docker==6.0.0 requests==2.28.1
```

Run the 'host-setup' Ansible playbook:

```
(local)$ make use-dev # development environment instead of production
(local)$ make host-setup
```

Build and push all Docker images:

```
(local)$ make all
(local)$ make push-all
```

Deploy containers from the latest images:

```
(local)$ make deploy
```

Check if the website is working by going to
[https://jammr.net/](https://jammr.net). Note that `make use-dev` modified
`/etc/hosts` so that jammr.net will resolve to the VM.
