#!/usr/bin/env python
# Copyright 2020 Stefan Hajnoczi <stefanha@gmail.com>

import subprocess
import schedule
import time

def apply_tax_rate_changes():
    subprocess.call(('bin/python', 'manage-website.py', 'apply_tax_rate_changes'))

schedule.every().day.at("00:01:00").do(apply_tax_rate_changes)

while True:
    schedule.run_pending()
    time.sleep(schedule.idle_seconds())
