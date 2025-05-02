To deploy to production:

1. First test the change in the development environment!
1. Run `make use-prod` to ensure the production environment is being used
   instead of the development environment.
1. Push the container image that was just tested in a development environment
   to the production server with `HOST=node1 make push-<name>`. The `HOST`
   environment variable limits the servers where the container image will be
   pushed and this is useful when pushing website changes that only affect the
   server running the website.
1. Deploy the new container image with `HOST=node1 make deploy`. Remove or
   adjust `HOST` depending on which servers should be affected.
1. Observe the logs with `ssh node1.jammr.net docker logs <container>`. Adjust
   the hostname depending on which server is being observed.
