#!/usr/bin/python3
import os
import docker

container_name = os.environ.get('NGINX_CONTAINER_NAME')

client = docker.from_env()
container = client.containers.get(container_name)
container.exec_run(['/usr/sbin/nginx', '-s', 'reload'])
