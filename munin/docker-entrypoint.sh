#!/bin/sh

# Run munin manually once to populate files needed by the fcgi scripts
/bin/su - munin --shell=/bin/sh -c /usr/bin/munin-cron

spawn-fcgi -a 0.0.0.0 -p 9000 -u www-data -g munin -- /usr/lib/munin/cgi/munin-cgi-html
spawn-fcgi -a 0.0.0.0 -p 9001 -u www-data -g munin -- /usr/lib/munin/cgi/munin-cgi-graph
exec cron -f
