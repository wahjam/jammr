# Copyright 2012 Stefan Hajnoczi <stefanha@gmail.com>

import json
import os
import re
import shutil
import random
import string
import datetime
from twisted.internet import reactor
from twisted.application import service
from twisted.python import log
import twisted.internet.error
import settings
import serverprocess

ISO8601_DATETIME_FMT = '%Y-%m-%dT%H:%MZ'

session_dir_re = re.compile(r'(?P<year>\d{4})(?P<month>\d{2})(?P<day>\d{2})_(?P<hour>\d{2})(?P<minute>\d{2})\.wahjam')

def get_session_start_date(session_dir):
    '''Return datetime.datetime object from a wahjamsrv session directory name'''
    m = session_dir_re.match(os.path.basename(session_dir))
    if not m:
        raise RuntimeError('unable to match session_dir datetime regex')
    return datetime.datetime(int(m.group('year')),
                             int(m.group('month')),
                             int(m.group('day')),
                             int(m.group('hour')),
                             int(m.group('minute')))


class Jam(service.Service):
    def __init__(self, port, topic, jamd, owner=None):
        self.port = port
        self.directory = os.path.join(settings.run_dir, 'jam-%s' % port)
        self.owner = owner
        self.topic = topic
        self.jamd = jamd
        self.serverProcess = None
        self.delayedStatusCall = None
        self.status_fired = False
        self.idle_time = 0
        self.idle_shutdown_enabled = True
        self.delay_before_idle_monitoring = None
        self.last_num_users = 0

    def startService(self):
        log.msg('Starting %s' % self)
        server_name = '%s:%s' % (settings.hostname, self.port)
        status_pass = ''.join(random.choice(string.ascii_letters + string.digits) for i in range(8))
        try:
            os.mkdir(self.directory, 0o755)
        except OSError:
            pass # probably already exists
        self.serverProcess = serverprocess.ServerProcess(settings.wahjamsrv_executable,
                {'Port': self.port,
                 'SessionArchive': '"%s" 60' % self.directory,
                 'DefaultTopic': '"%s"' % self.topic,
                 'DefaultBPM': '%s' % settings.default_bpm,
                 'DefaultBPI': '%s' % settings.default_bpi,
                 'SetVotingThreshold': '1',
                 'SetVotingVoteTimeout': '120',
                 'JammrApi': '%s %s %s %s' % (settings.api_url, settings.api_username, settings.api_password, server_name),
                 'StatusUserPass': 'status %s' % status_pass,
                 'SslVerify': 'yes' if settings.ssl_verify else 'no'},
                os.path.join(self.directory, 'config'),
                self.sessionFinished,
                self.serverProcessEnded)
        self.serverProcess.start() # TODO what if this fails?
        self.delayedStatusCall = reactor.callLater(2, self.getStatus)

        if not self.isPublic():
            self.enableIdleShutdown(False)
            self.delay_before_idle_monitoring = reactor.callLater(settings.private_jam_join_grace_time, self.startIdleMonitoring)

        return service.Service.startService(self)

    def stopService(self):
        log.msg('Stopping %s' % self)
        if self.delay_before_idle_monitoring is not None:
            self.delay_before_idle_monitoring.cancel()
            self.delay_before_idle_monitoring = None
        if self.delayedStatusCall is not None:
            self.delayedStatusCall.cancel()
            self.delayedStatusCall = None
        if self.serverProcess:
            self.serverProcess.stop()
            self.serverProcess = None

        server = '%s:%s' % (settings.hostname, self.port)
        self.jamd.getRedis().delete('livejams/%s' % server)
        self.jamd.getRedis().delete('acls/%s' % server)

        if self.isPublic() and self.last_num_users > 0:
            self.jamd.getRedis().incr('num_public_users', amount=-self.last_num_users)
            self.last_num_users = 0

        try:
            shutil.rmtree(self.directory)
        except OSError:
            pass # ignore
        return service.Service.stopService(self)

    def __str__(self):
        return '<%s jam %s on port %s>' % ('Public' if self.isPublic() else 'Private',
                id(self), self.port)

    def startIdleMonitoring(self):
        self.delay_before_idle_monitoring = None
        self.enableIdleShutdown(True)

    def getStatus(self):
        self.delayedStatusCall = None
        self.serverProcess.getStatus().addCallback(self.gotStatus).addErrback(self.gotStatusErr)

    def gotStatus(self, status):
        self.status_fired = True

        status['server'] = '%s:%s' % (settings.hostname, self.port)
        status['is_public'] = self.isPublic()

        num_users = len(set(status['users']).difference(settings.bot_ignore_list))

        # Publish user count only for public jam sessions
        if num_users != self.last_num_users and self.isPublic():
            self.jamd.getRedis().incr('num_public_users', amount=(num_users - self.last_num_users))
            self.last_num_users = num_users

        if num_users == 0:
            self.idle_time += settings.status_update_interval
            if self.idle_shutdown_enabled and self.idle_time >= settings.idle_shutdown_time:
                if self.jamd.shouldDestroyIdleJam(self):
                    log.msg('Destroying idle jam %s' % self)
                    self.jamd.destroyJam(self)
                    return
        else:
            old_idle_time = self.idle_time
            self.idle_time = 0
            if old_idle_time > 0:
                # Call after setting idle_time so isEmpty() is False
                self.jamd.firstUserJoined(self)

        if self.idle_shutdown_enabled and self.idle_time >= settings.idle_stealth_time and self.jamd.shouldDestroyIdleJam(self):
            # Do not publish status for idle jams once they reach a threshold.
            # This decreases the chance that users will try to connect to a jam
            # that doesn't exist due to stale status info.
            self.jamd.getRedis().delete('livejams/%s' % status['server'])
        else:
            self.jamd.getRedis().set('livejams/%s' % status['server'], json.dumps(status),
                                     expire=settings.status_update_interval * 2)

        self.delayedStatusCall = reactor.callLater(settings.status_update_interval, self.getStatus)

    def gotStatusErr(self, err):
        log.msg('Failed to get status for %s: %s' % (self, err))
        self.jamd.destroyJam(self)

    def enableIdleShutdown(self, enable):
        self.idle_shutdown_enabled = enable

    def isPublic(self):
        return self.owner is None

    def isEmpty(self):
        return self.idle_time > 0 or not self.status_fired

    def sessionFinished(self, session_dir):
        session_dir = os.path.normpath(session_dir)

        # Move to recorded-jams directory so jam run directory can be deleted
        # if the server process terminates.
        jams_dir = os.path.join(os.path.normpath(settings.run_dir), 'session-archive')
        try:
            os.mkdir(jams_dir, 0o755)
        except OSError:
            pass # probably already exists

        start_date = get_session_start_date(session_dir)

        # Add wahjamsrv port to directory name to make it unique
        dest_dir = os.path.join(jams_dir, '%s_%s.wahjam' % (start_date.strftime('%Y%m%d_%H%M'), self.port))
        shutil.move(session_dir, dest_dir)

        # Write jam descriptor file, recorded_jamsd will pick it up when we
        # close the file.
        json_path = os.path.join(jams_dir, os.path.basename(dest_dir) + '.json')
        with open(json_path, 'wt') as f:
            data = {
                'session_dir': dest_dir,
                'start_date': start_date.strftime(ISO8601_DATETIME_FMT),
                'server': '%s:%s' % (settings.hostname, self.port),
            }
            if self.owner is not None:
                data['owner'] = self.owner
            json.dump(data, f)

    def serverProcessEnded(self):
        self.serverProcess = None
        self.jamd.destroyJam(self)
