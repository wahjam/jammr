#!/usr/bin/env python
# Copyright 2023 Stefan Hajnoczi <stefanha@gmail.com>

import subprocess
import schedule
import time

def clear_sessions():
    subprocess.call(('bin/python', 'manage-website.py', 'clearsessions'))

schedule.every().day.at("00:02:00").do(clear_sessions)

while True:
    schedule.run_pending()
    time.sleep(schedule.idle_seconds())
