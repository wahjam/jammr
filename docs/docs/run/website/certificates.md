Website and REST API traffic is only over HTTPS. TLS certificates are required
for HTTPS.

Configuring certificates
------------------------
The `nginx-https` container has a volume that contains the files
`jammr.net.crt` and `jammr.net.key` for the certificate. These files are copied
from `nginx/jammr.net-<env>.crt` where `env` is the deployment environment
(`prod` for production or `dev` for development). A self-signed certificate is
included for the `dev` environment and a commercial certificate is included for
the `prod` environment.

Enabling Let's Encrypt
----------------------
It is also possible to use [Let's Encrypt](https://letsencrypt.org/) by setting
`certbot_enabled` to `true` in the `inventories/<env>/group_vars/all` file,
where `env` is the deployment environment (`prod` for production). In the past
some users reported issues with Let's Encrypt on old Windows machines, but
recent operating systems should have the necessary CA certificates to trust
Let's Encrypt.
