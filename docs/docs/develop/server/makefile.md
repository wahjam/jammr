A `Makefile` handles common development and deployment tasks. It typically
calls Ansible to configure remote servers, avoiding the need to manually invoke
Ansible.

Containers
----------

- `make all|certbot|exim4|jamd|munin|openssh-client|recorded-jams|webapp` -
  Build container images. Note that images are built locally and still need to
  be pushed to servers in order to deploy them.

- `make push-all|push-...` - Push a container image to a server. Note that this
  does not restart containers, so make sure to run the `deploy` target
  afterwards.

- `make deploy` - Restart containers on servers from the latest pushed images
  with the latest configuration files. It is often useful to use `HOSTS=node1 make deploy`
  to only deploy to specific hosts like `node1`.

Client releases
---------------

- `make client-mac|client-windows` - Build macOS and Windows clients.

- `make deploy-client` - Publish a new release of the client.

Server setup
------------

- `make host-setup` - Install and configure a remote host.

- `make setup-backup` - Set up database backups to an off-site server.

Environments
------------

- `make use-dev|use-prod` - Switch between the development and staging environment.
