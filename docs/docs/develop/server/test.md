Deploying changes
-----------------
To deploy changes to a development environment:

1. Run `make use-dev` to ensure the development environment is being used
   instead of the production environment.
1. Build the new container image for the modified component with `make <name>`.
   For example, `make webapp` for the website and forum container image. See
   `make help` for a full list of container images.
1. Push the newly built container image to the development server with `make push-<name>`.
1. Deploy the new container image with `make deploy`.
1. Observe the logs with `ssh dev1.jammr.net docker logs <container>`.

Running automated tests
-----------------------
To run automated tests:

1. After deploying changes, ssh into the development server: `ssh dev1.jammr.net`.
1. Run the tests in the appropriate container. For example, to run the website tests: `docker exec -it website ./manage-website.py test`.

Connecting a client for manual testing
--------------------------------------
To connect the client to the server, make sure that each machine running a
client has `/etc/hosts` configured so `jammr.net` resolves to the IP address of
the development server.

Simulating users in a jam session
---------------------------------
A bot is available for simulating users in a jam session:

```
(local)$ bin/python jamd/bot.py --host dev1.jammr.net <username> <password> <song-file>
```

A song file is a JSON file describing the audio intervals to upload. Several
song files are available to simulate different scenarios.
