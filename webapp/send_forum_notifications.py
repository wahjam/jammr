#!/usr/bin/env python
# Copyright 2019 Stefan Hajnoczi <stefanha@gmail.com>

import subprocess
import schedule
import time

def send_forum_notifications():
    subprocess.call(('bin/python', 'manage-forum.py', 'email_notifications'))

schedule.every().day.at("00:01:00").do(send_forum_notifications)

while True:
    schedule.run_pending()
    time.sleep(schedule.idle_seconds())
