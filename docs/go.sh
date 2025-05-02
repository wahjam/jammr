#!/bin/bash
cd "$(dirname $0)"

DOCKER=${DOCKER:-docker}

"$DOCKER" build --tag jammr-docs .
exec "$DOCKER" run -it --rm -v .:/docs:z -p 8000:8000 jammr-docs

