#!/usr/bin/env python3
# Copyright 2013-2020 Stefan Hajnoczi <stefanha@gmail.com>

import os
import sys
import argparse
import datetime
import logging
import zipfile
import string
import random
import shutil
import settings
import mix
import upload
import jammr_api

logging.basicConfig(level=logging.DEBUG)
logging.getLogger('boto').setLevel(logging.WARNING)
log = logging.getLogger(__name__)

ISO8601_DATETIME_FMT = '%Y-%m-%dT%H:%MZ'

def random_cookie():
    '''Return random 10-character string'''
    return ''.join(random.choice(string.ascii_letters + string.digits) for x in range(10))

def get_users_from_clipsort_log(path):
    '''Parse a clipsort.log file and return the set of users'''
    users = set()
    with open(path, 'rt') as clipsort_log:
        for line in clipsort_log:
            fields = line.rstrip().split()
            if len(fields) != 5:
                continue
            if fields[0] != 'user':
                continue
            username = fields[2].strip('"')
            users.add(username)
    return users

def archive_jam(session_dir, start_date):
    # Concat interval files into per-user tracks
    rc = mix.cliplogcvt(session_dir)
    if rc != 0:
        log.error('cliplogcvt %s failed with exit code %d' % (session_dir, rc))
        sys.exit(rc)

    concat_dir = os.path.join(session_dir, 'concat')
    concat_filenames = []
    users = set()
    for filename in os.listdir(concat_dir):
        concat_filenames.append(os.path.join(concat_dir, filename))
        users.add(filename.rsplit('_', 1)[0])

    log.info('%d tracks for users: %s' % (len(concat_filenames), ', '.join(users)))

    if users:
        # Log clipsort.log for debugging
        log.info('clipsort.log contents:')
        with open(os.path.join(session_dir, 'clipsort.log'), 'rt') as clipsort:
            for line in clipsort:
                log.info(line.strip())
        log.info('End of clipsort.log')

        # Generate random filenames that are hard to guess.  The mix may be public
        # but tracks may not be, so use different random cookies.
        output_prefix = os.path.join(session_dir, start_date.strftime('%Y%m%d_%H%M'))
        mix_filename = '%s_%s.m4a' % (output_prefix, random_cookie())
        tracks_filename = '%s_%s.zip' % (output_prefix, random_cookie())

        # Write zip file with per-user tracks
        with zipfile.ZipFile(tracks_filename, 'w', zipfile.ZIP_DEFLATED) as tracks_zip:
            for track_filename in concat_filenames:
                tracks_zip.write(track_filename, os.path.basename(track_filename))

        # Mix down all tracks into an m4a file
        rc = mix.mix(concat_filenames, mix_filename)
        if rc != 0:
            log.error('ffmpeg failed with exit code %d' % rc)
            sys.exit(rc)

        # Delete track files
        for track_filename in concat_filenames:
            os.remove(track_filename)

        duration = mix.get_duration(mix_filename)

        add_recorded_jam = True
        if duration < settings.min_duration:
            log.info('Not adding recorded jam with {} duration'.format(duration))
            add_recorded_jam = False

        if add_recorded_jam:
            if settings.skip_upload:
                mix_url = 'https://test.jammr.net/mix.m4a'
                tracks_url = 'https://test.jammr.net/tracks.zip'
            else:
                upload.override_socket_priority()
                mix_url, tracks_url = upload.upload(settings.s3_host, settings.s3_access_key, settings.s3_secret_key,
                                                    settings.s3_bucket, [mix_filename, tracks_filename],
                                                    use_multipart_upload=settings.s3_multipart_upload)
            log.info('Uploaded mix to %s' % mix_url)
            log.info('Uploaded tracks to %s' % tracks_url)

        if args.delete:
            os.remove(mix_filename)
            os.remove(tracks_filename)

        if add_recorded_jam:
            jammr_api.add_recorded_jam(start_date, users, args.owner, mix_url, tracks_url, duration, args.server)


parser = argparse.ArgumentParser(description='Archive jam sessions.')
parser.add_argument('--owner', help='private jam session owner username')
parser.add_argument('--delete', action='store_true', help='delete session on successful completion')
parser.add_argument('session_dir', help='jam session directory (with clipsort.log)')
parser.add_argument('start_date', help='jam session directory (with clipsort.log)')
parser.add_argument('server', help='server where jam took place (host:port)')

if __name__ == '__main__':
    args = parser.parse_args()
    session_dir = os.path.normpath(args.session_dir)
    start_date = datetime.datetime.strptime(args.start_date, ISO8601_DATETIME_FMT)

    log.info('Archiving \'%s\' with start date %s...' % (session_dir, start_date.strftime('%Y-%m-%d %H:%M')))

    # The set of users that sent audio
    cliplog_users = get_users_from_clipsort_log(os.path.join(session_dir, 'clipsort.log'))
    log.info('Users that sent audio: %s' % ', '.join(cliplog_users))

    # Users that sent audio plus the jam session owner, if any
    all_users = set(cliplog_users)
    if args.owner:
        all_users.add(args.owner)

    if jammr_api.can_access_recorded_jams(all_users) and cliplog_users:
        archive_jam(session_dir, start_date)
    else:
        log.info('Not archiving jam')

    if args.delete:
        shutil.rmtree(session_dir)
