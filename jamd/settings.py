import os
import socket

# Redis server connection details
redis_addr = ('redis', 6379)

# Hostname for wahjamsrv sessions
hostname = os.environ.get('EXTERNAL_HOSTNAME') or socket.getfqdn()

# Development environment or production?
debug = hostname.startswith('dev')
staging = hostname == 'staging.jammr.net'

# Jammr API
if staging:
    api_url = 'https://staging.jammr.net/api/'
else:
    api_url = 'https://jammr.net/api/'
api_username = 'wahjamsrv'
api_password = os.environ.get('JAMMR_API_PASSWORD')

# Verify SSL certificates?
ssl_verify = True
if debug or staging:
    ssl_verify = False

# First TCP port to bind wahjamsrv instances
base_port = 10100

# Path to wahjamsrv executable
wahjamsrv_executable = '/home/jamd/bin/wahjamsrv'

# Directory to store jam configs and session archives
run_dir = '/tmp/'

# Maximum number of jams
max_jams = int(os.environ.get('MAX_JAMS', 48))

# Number of empty public jams
empty_public_jams = 2

# Default public jam topic
default_public_jam_topic = 'Public jam - Play nicely'

# Tempo and interval length
default_bpm = 120
default_bpi = 16

# Number of seconds between jam status updates
status_update_interval = 45

# Number of seconds before ceasing status reports for empty jams
idle_stealth_time = 60

# Number of seconds before shutting down empty jams
idle_shutdown_time = 90

# Number of seconds grace time for private jam owner to join
private_jam_join_grace_time = 60

# List of usernames to ignore for idle check
bot_ignore_list = []
