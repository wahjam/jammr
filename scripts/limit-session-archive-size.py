#!/usr/bin/env python3
# Delete session archives if the file system is running low on space

import os
import shutil
import time

session_dir = '/opt/volumes/session-archive'
reserved_size = 2 * 1024 * 1024 * 1024

progress = True
while True:
    if not progress:
        time.sleep(60)
    progress = False

    st = os.statvfs(session_dir)
    if st.f_bfree * st.f_bsize >= reserved_size:
        continue

    sessions = sorted(x[:-len('.json')] for x in os.listdir(session_dir) if x.endswith('.json'))
    if len(sessions) <= 2:
        continue

    session = sessions.pop()

    try:
        os.remove(os.path.join(session_dir, session + '.json'))
    except:
        pass

    try:
        shutil.rmtree(os.path.join(session_dir, session))
    except:
        pass

    progress = True
