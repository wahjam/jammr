import os
import socket
import datetime

hostname = os.environ.get('EXTERNAL_HOSTNAME') or socket.getfqdn()
debug = hostname.startswith('dev')
staging = hostname == 'staging.jammr.net'

# DreamObjects account information
s3_host = 'objects-us-east-1.dream.io'
s3_access_key = os.environ.get('S3_ACCESS_KEY')
s3_secret_key = os.environ.get('S3_SECRET_KEY')
if staging:
    s3_bucket = 'jammr-staging'
else:
    s3_bucket = 'jammr'
s3_multipart_upload = True

# ffmpeg-like program name
avprog = 'ffmpeg'
avprobe = 'ffprobe'

# cliplogcvt program name
cliplogcvt = '/home/recorded_jams/bin/cliplogcvt'

# how many jams to convert in parallel
max_processes = int(os.environ.get('MAX_PROCESSES', 2))

# jammr REST API
if staging:
    jammr_api_url = 'https://staging.jammr.net/api/'
else:
    jammr_api_url = 'https://jammr.net/api/'
jammr_user = 'recorded_jams'
jammr_password = os.environ.get('JAMMR_API_PASSWORD')

# Verify SSL certificates?
ssl_verify = True
if debug or staging:
    ssl_verify = False

session_archive_path = '/tmp/session-archive'

# Delete session directory after successful upload
delete_on_success = not debug

# Skip cloud storage upload (for testing)
skip_upload = debug

# Skip jams shorter than this time
min_duration = datetime.time(0, 5, 0)
