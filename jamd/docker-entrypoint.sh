#!/bin/bash
ulimit -c unlimited

# Remove pidfile if container was interrupted due to power loss
rm -f twistd.pid

PYTHONPATH=$(realpath $(dirname $0)) exec bin/twistd --nodaemon --logfile - --python jamd.tac
