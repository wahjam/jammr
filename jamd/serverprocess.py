# Copyright 2012 Stefan Hajnoczi <stefanha@gmail.com>

import os
import re
import twisted.internet
import twisted.internet.error
import twisted.internet.protocol
import twisted.protocols.basic
from twisted.internet import reactor, defer
from twisted.python import log
from protocol import JammrProtocol, LoginFailed

archive_re = re.compile(r'Finished archiving session \'([^\']+)\'')

class StatusClient(JammrProtocol):
    def serverAuthReply(self, msg):
        self.transport.loseConnection()
        self.factory.deferred.errback(LoginFailed(msg.errmsg))

    def serverUserInfoChangeNotify(self, msg):
        self.serverUserInfoChangeNotify = msg

    def serverConfigChangeNotify(self, msg):
        self.serverConfigChangeNotify = msg

    def chatMessage(self, msg):
        if msg.parms[0] == 'TOPIC':
            self.topic = msg
        elif msg.parms[0] == 'USERCOUNT':
            users = set()
            for userinfo in self.serverUserInfoChangeNotify.recs:
                if not userinfo.is_active:
                    continue
                users.add(userinfo.username)

            data = {'users': list(users),
                    'bpm': self.serverConfigChangeNotify.bpm,
                    'bpi': self.serverConfigChangeNotify.bpi,
                    'topic': self.topic.parms[2],
                    'numusers': msg.parms[1],
                    'maxusers': msg.parms[2]}

            self.transport.loseConnection()
            self.factory.deferred.callback(data)

class StatusFactory(twisted.internet.protocol.ClientFactory):
    protocol = StatusClient

    def __init__(self, username, password, deferred):
        self.username = username
        self.password = password
        self.deferred = deferred

class ServerProcessProtocol(twisted.internet.protocol.ProcessProtocol):
    service = None
    name = None
    linebuf = []

    def outReceived(self, data):
        data = data.decode('utf-8')
        while '\n' in data:
            eol, data = data.split('\n', 1)
            line = ''.join(self.linebuf + [eol])
            self.linebuf = []
            self.lineReceived(line)
        if data:
            self.linebuf.append(data)

    errReceived = outReceived

    def lineReceived(self, line):
        log.msg('[%s] %s' % (self.name, line))

        m = archive_re.search(line)
        if m:
            session_dir = m.group(1)
            self.service.sessionFinished(session_dir)

    def processEnded(self, reason):
        if self.linebuf:
            self.lineReceived(''.join(self.linebuf))
            self.linebuf = []
        if reason.value.exitCode == 0:
            log.msg('[%s] Exited successfully' % self.name)
        else:
            log.msg('[%s] Terminated with error: %s' % (self.name, reason.value))
        self.service.connectionLost(self.name)

class ServerProcess(object):
    def __init__(self, executable, config, config_path, sessionFinished, processEnded):
        self.executable = executable
        self.config = config
        self.config_path = config_path
        self.sessionFinished = sessionFinished
        self.processEnded = processEnded

    def _write_config(self):
        data = '\n'.join(['%s %s' % (k, v) for k, v in self.config.items()]) + '\n'
        try:
            open(self.config_path, 'w').write(data)
        except IOError:
            log.err()
            return False
        return True

    def _delete_config(self):
        try:
            os.remove(self.config_path)
        except OSError:
            log.err()

    def start(self):
        if not self._write_config():
            return

        # TODO privilege dropping

        proto = ServerProcessProtocol()
        proto.service = self
        proto.name = 'wahjamsrv:%s' % (self.config['Port'])
        self.transport = reactor.spawnProcess(proto, self.executable,
                args=['wahjamsrv', self.config_path],
                env=os.environ)

    def stop(self):
        # Don't call back if we're expecting to be terminated
        self.processEnded = None

        try:
            self.transport.signalProcess('INT')
        except twisted.internet.error.ProcessExitedAlready:
            pass

    def connectionLost(self, name):
        # TODO delete config file
        if self.processEnded:
            self.processEnded()

    def getPort(self):
        return self.config['Port']

    def getStatus(self):
        if 'StatusUserPass' not in self.config:
            log.msg('Unable to get server process status because StatusUserPass config is missing')
            return
        if 'Port' not in self.config:
            log.msg('Unable to get server process status because Port config is missing')
            return
        username, password = self.config['StatusUserPass'].split()
        d = defer.Deferred()
        f = StatusFactory(username, password, d)
        reactor.connectTCP('127.0.0.1', self.config['Port'], f)
        return d
