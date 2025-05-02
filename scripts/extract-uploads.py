#!/usr/bin/env python3
# Dump audio from a jam session TCP stream (e.g. from Wireshark)

import os
import sys
import struct

MESSAGE_CLIENT_UPLOAD_INTERVAL_BEGIN = 0x83
MESSAGE_CLIENT_UPLOAD_INTERVAL_WRITE = 0x84


files = {}


def parseClientUploadIntervalBegin(data):
    if len(data) < 25:
        raise ValueError('MESSAGE_CLIENT_UPLOAD_INTERVAL_BEGIN too short')
    guid = data[:16].hex()
    estsize = struct.unpack('<I', data[16:20])[0]
    fourcc = struct.unpack('<I', data[20:24])[0]
    chidx = struct.unpack('<B', data[24:25])[0]

    dirname = guid[0]
    try:
        os.mkdir(dirname)
    except FileExistsError:
        pass

    filename = '{}/{}.ogg'.format(guid[0], guid)
    files[guid] = open(filename, 'wb')

    print('interval 0 120 16')
    print('user {} "username" {} channel'.format(guid, chidx))


def parseClientUploadIntervalWrite(data):
    if len(data) < 17:
        raise ValueError('MESSAGE_CLIENT_UPLOAD_INTERVAL_WRITE too short')
    guid = data[:16].hex()
    flags = struct.unpack('<B', data[16:17])[0]
    audio_data = data[17:]

    files[guid].write(audio_data)

    if flags & 0x1:
        del files[guid]


def readMessage(f):
    data = f.read(5)
    if len(data) != 5:
        return False

    msgtype, length = struct.unpack('<BI', data)
    data = f.read(length)

    if msgtype == MESSAGE_CLIENT_UPLOAD_INTERVAL_BEGIN:
        parseClientUploadIntervalBegin(data)
    elif msgtype == MESSAGE_CLIENT_UPLOAD_INTERVAL_WRITE:
        parseClientUploadIntervalWrite(data)

    return True


filename = sys.argv[1]
with open(filename, 'rb') as f:
    while readMessage(f):
        pass
