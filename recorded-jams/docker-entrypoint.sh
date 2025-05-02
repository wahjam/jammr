#!/bin/bash
ulimit -c unlimited

# Remove pidfile if container was interrupted due to power loss
rm -f twistd.pid

PYTHONPATH=$(realpath $(dirname $0)) exec nice --adjustment 19 bin/twistd --nodaemon --logfile - --python recorded_jamsd.tac
