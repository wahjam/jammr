#!/usr/bin/env python3
#
# Mix audio segments into an MP4 (AAC) using ffmpeg.
#
# Copyright 2013 Stefan Hajnoczi <stefanha@gmail.com>

import os
import subprocess
import logging
import json
import datetime
import settings

__all__ = ['mix', 'cliplogcvt', 'get_duration']
log = logging.getLogger(__name__)

def preexec_nice_down():
    '''Set the process scheduling priority to the lowest priority'''
    os.nice(19)

def mix(input_filenames, output_filename):
    '''Mix tracks down into a single output audio file'''
    args = [settings.avprog]

    for infile in input_filenames:
        args.extend(('-i', infile))

    inputs = ''.join('[%d]' % i for i in range(len(input_filenames)))
    args.extend(('-filter_complex', '%s amix=normalize=false:inputs=%d [a]' % (inputs, len(input_filenames))))
    args.extend(('-map', '[a]'))
    args.extend(('-strict', 'experimental'))
    args.extend(('-loglevel', 'error'))
    args.append('-y') # overwrite output files without asking
    args.append(output_filename)

    log.info(' '.join(args))
    return subprocess.call(args, preexec_fn=preexec_nice_down)

def cliplogcvt(session_dir):
    '''Concatenate tracks from interval files into concat/ directory'''
    args = [settings.cliplogcvt, session_dir]
    log.info(' '.join(args))
    return subprocess.call(args, preexec_fn=preexec_nice_down)

def get_duration(filename):
    '''Return duration (datetime.time) for an audio file'''
    args = [
        settings.avprobe,
        '-loglevel', 'error',
        '-show_format',
        '-print_format', 'json',
        '-i', filename
    ]
    log.info(' '.join(args))
    process = subprocess.Popen(args, stdout=subprocess.PIPE, preexec_fn=preexec_nice_down)
    data, _ = process.communicate()
    if process.returncode != 0:
        return datetime.time(0, 0)

    data = json.loads(data)
    secs = float(data['format']['duration'])
    if secs >= 60 * 60:
        hours = int(secs / (60 * 60))
        secs -= hours * (60 * 60)
    else:
        hours = 0
    if secs >= 60:
        minutes = int(secs / 60)
        secs -= minutes * 60
    else:
        minutes = 0
    return datetime.time(hours, minutes, int(secs))
