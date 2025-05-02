The server-side components include the website, REST API, jam sessions, and
recorded jam processing. In addition, there are several services like outgoing
email (Exim), database (PostgreSQL), and Redis that underlie these components.

![jammr architecture](../../images/jammr-architecture.png)

Each component runs in a [Docker
container](https://www.docker.com/resources/what-container/) on a
[Debian](https://www.debian.org/) server. Keeping everything inside containers
make it easier to test and deploy components in isolation without worrying
about dependencies on the server's environment.

Most of the CPU- and network-intensive work happens in the jam session and
recorded jam processing components. These scale horizontally, so it's possible
to add more servers to meet capacity requirements. In a development environment
or a small production environment there might be just one server. If there are
many active jam sessions in a production environment then it may be necessary
to have several servers handling the load.

Servers are managed using
[Ansible](https://docs.ansible.com/ansible/latest/index.html), an automation
tool that remotely configures servers. The `playbooks/host-setup.yml` playbook
bootstraps a server given root access to a minimal Debian server. The
`playbooks/deploy.yml` playbook (re)starts containers and needs to be run every
time the container images or configuration files have been changed. However,
most of the time the [Makefile](makefile.md) provides a more convenient
command-line interface than invoking Ansible directly.
