# Copyright 2013 Stefan Hajnoczi <stefanha@gmail.com>

import os
import sys
import json
from twisted.application import service
from twisted.internet import reactor, inotify, error
from twisted.python import log, filepath
import twisted.internet.protocol
import settings

class LoggingProcessProtocol(twisted.internet.protocol.ProcessProtocol):
    service = None
    name = None
    linebuf = []

    def outReceived(self, data):
        while b'\n' in data:
            eol, data = data.split(b'\n', 1)
            line = b''.join(self.linebuf + [eol])
            self.linebuf = []
            self.lineReceived(line.decode('utf-8'))
        if data:
            self.linebuf.append(data)

    errReceived = outReceived

    def lineReceived(self, line):
        log.msg('[%s] %s' % (self.name, line))

    def processEnded(self, reason):
        if self.linebuf:
            self.lineReceived(''.join(self.linebuf))
            self.linebuf = []
        self.service.archiveFinished(self.name, reason)

class RecordedJamsdService(service.Service):
    def __init__(self):
        self.notifier = inotify.INotify()
        self.pending = []
        self.processes = {}

        try:
            os.mkdir(settings.session_archive_path, 0o755)
        except OSError:
            pass # probably already exists

    def startService(self):
        service.Service.startService(self)

        self.notifier.startReading()
        self.notifier.watch(filepath.FilePath(settings.session_archive_path),
                            callbacks=[self.notify],
                            mask=inotify.IN_CLOSE_WRITE | inotify.IN_MOVED_TO)

        self.scan_existing_jams()

    def stopService(self):
        self.notifier.ignore(filepath.FilePath(settings.session_archive_path))
        self.notifier.stopReading()

        for transport in list(self.processes.values()):
            transport.signalProcess('TERM')
        self.processes.clear()

        service.Service.stopService(self)

    def notify(self, _, path, mask):
        '''inotify handler function'''
        path = path.asTextMode()
        if not path.path.endswith('.json'):
            return
        if mask & inotify.IN_CLOSE_WRITE or mask & inotify.IN_MOVED_TO:
            self.add_jam(path)

    def scan_existing_jams(self):
        '''Check for existing sessions while we were not running'''
        archive = filepath.FilePath(settings.session_archive_path)
        for path in archive.globChildren('*.json'):
            if path.isdir():
                continue
            self.add_jam(path)

    def next_jam(self):
        while self.pending and len(self.processes) < settings.max_processes:
            path = self.pending.pop(0)
            self.archive_jam(path)

    def add_jam(self, path):
        self.pending.append(path)
        self.next_jam()

    def archive_jam(self, path):
        name = path.basename().strip('.wahjam.json')
        if name in self.processes:
            return

        log.msg('Opening new session at %s' % path.path)
        try:
            data = json.load(path.open())
        except ValueError:
            log.err()
            return
        for attr in ('server', 'session_dir', 'start_date'):
            if attr not in data:
                log.msg('Jam JSON missing "%s" attribute: %s' % (attr, data))
                return

        proto = LoggingProcessProtocol()
        proto.service = self
        proto.name = name

        # Use current python executable to keep virtualenv (if active)
        executable = sys.executable
        args = [sys.executable,
                os.path.join(os.path.dirname(os.path.realpath(__file__)), 'archive-jam.py')]
        if 'owner' in data:
            args.append('--owner=' + data['owner'])
        if settings.delete_on_success:
            args.append('--delete')
        args.extend((
            data['session_dir'],
            data['start_date'],
            data['server']
        ))
        log.msg('[%s] %s' % (name, ' '.join(args)))
        transport = reactor.spawnProcess(proto, executable, args=args, env=None)
        self.processes[name] = transport

    def archiveFinished(self, name, reason):
        if name not in self.processes:
            return

        log.msg('[%s] terminated' % name)

        if reason.check(error.ProcessDone) and settings.delete_on_success:
            os.remove(os.path.join(settings.session_archive_path, name + '.wahjam.json'))

        del self.processes[name]
        self.next_jam()

application = service.Application("recorded_jamsd")
recorded_jamsd_service = RecordedJamsdService()
recorded_jamsd_service.setServiceParent(application)
