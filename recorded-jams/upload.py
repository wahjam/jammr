#!/usr/bin/env python3
# Copyright 2013 Stefan Hajnoczi <stefanha@gmail.com>

import sys
import os.path
import socket
from boto.s3.connection import S3Connection
from boto.s3.key import Key

__all__ = ['upload', 'override_socket_priority']

MULTIPART_SIZE = 8 * 1024 * 1024

def multipart_upload(bucket, basename, filename):
    '''Upload file using S3 Multipart Upload (better reliability for large files)'''
    multi = bucket.initiate_multipart_upload(basename, policy='public-read')
    with open(filename, 'rb') as fp:
        fp.seek(0, os.SEEK_END)
        total_size = fp.tell()
        fp.seek(0, os.SEEK_SET)

        offset = 0
        while offset < total_size:
            part_num = 1 + (offset // MULTIPART_SIZE)
            size = min(MULTIPART_SIZE, total_size - offset)
            multi.upload_part_from_file(fp, part_num, size=size)
            offset += size
    multi.complete_upload()

def upload(s3_host, s3_access_key, s3_secret_key, s3_bucket, filenames,
           use_multipart_upload=True):
    conn = S3Connection(s3_access_key, s3_secret_key, host=s3_host)
    bucket = conn.get_bucket(s3_bucket, validate=False)

    urls = []
    for filename in filenames:
        basename = os.path.basename(filename)
        if use_multipart_upload:
            multipart_upload(bucket, basename, filename)
        else:
            k = Key(bucket, basename)
            k.set_contents_from_filename(filename, policy='public-read')
        urls.append('https://%s/%s/%s' % (s3_host, s3_bucket, basename))
    return urls

def override_socket_priority():
    '''Force all opened TCP sockets to have priority TC_PRIO_FILLER'''
    old_socket = socket.socket

    def new_socket(family=2, type=1, proto=0):
        s = old_socket(family, type, proto)
        if family == socket.AF_INET and type == socket.SOCK_STREAM and proto == 0:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_PRIORITY, 1)
        return s

    socket.socket = new_socket

if __name__ == '__main__':
    access_key, secret_key = sys.argv[1], sys.argv[2]
    bucket_name = sys.argv[3]

    print(upload('objects-us-east-1.dream.io', access_key, secret_key,
                 bucket_name, sys.argv[4:]))
