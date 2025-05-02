# Copyright 2012 Stefan Hajnoczi <stefanha@gmail.com>

import struct
from hashlib import sha1
from collections import namedtuple
from twisted.internet import protocol, reactor
from twisted.python import log
import settings

class InvalidMessageType(Exception):
    def __init__(self, msgtype):
        self.msgtype = msgtype

    def __str__(self):
        return 'Invalid message type: %#02x' % self.msgtype

class LoginFailed(Exception):
    def __init__(self, errmsg):
        Exception.__init__(self, errmsg)

class ServerAuthChallengeRequest(object):
    msgtype = 0x00

    def __init__(self, challenge, server_caps, protocol_version, license=None):
        self.challenge = challenge
        self.server_caps = server_caps
        self.protocol_version = protocol_version
        if server_caps & 1:
            self.license = license

    @staticmethod
    def parse(data):
        challenge = data[:8]
        server_caps, protocol_version = struct.unpack('<II', data[8:16])
        license = None
        if server_caps & 1:
            end = data[16:].find(b'\x00')
            if end != -1:
                license = data[16:16 + end].decode('utf-8')
        return ServerAuthChallengeRequest(challenge, server_caps, protocol_version, license)

class ClientAuthUser(object):
    msgtype = 0x80

    CAPS_ACCEPT_LICENSE = 0x01
    CLIENT_VERSION = 0x80000000 # NINJAM would be 0x00020000

    def __init__(self, passhash, username, client_caps, client_version):
        self.passhash = passhash
        self.username = username
        self.client_caps = client_caps
        self.client_version = client_version

    def build(self):
        return self.passhash + \
               self.username.encode('utf-8') + b'\x00' + \
               struct.pack('<II', self.client_caps, self.client_version)

class ServerAuthReply(object):
    msgtype = 0x01

    def __init__(self, flag, errmsg=None, maxchan=32):
        self.flag = flag
        self.errmsg = errmsg
        self.maxchan = maxchan

    @staticmethod
    def parse(data):
        flag, = struct.unpack('<B', data[:1])
        idx = data.find(b'\x00', 1)
        if idx == -1:
            return ServerAuthReply(flag)
        errmsg = data[1:idx].decode('utf-8')
        maxchan, = struct.unpack('<B', data[idx + 1:])
        return ServerAuthReply(flag, errmsg, maxchan)

class ClientSetChannelInfo(object):
    msgtype = 0x82

    ChannelInfo = namedtuple('ChannelInfo', ['name', 'volume', 'pan', 'flags'])

    def __init__(self, channelInfo):
        self.channelInfo = channelInfo

    def build(self):
        data = [struct.pack('<H', 4)] # channel parameter size
        for ch in self.channelInfo:
            name = ch.name.encode('utf-8')
            data.append(struct.pack('<%dsHbB' % (len(name) + 1),
                                    name, ch.volume, ch.pan, ch.flags))
        return b''.join(data)

class ServerUserInfoChangeNotify(object):
    msgtype = 0x03

    UserInfoChange = namedtuple('UserInfoChange', ['is_active', 'channel_id', 'volume', 'pan', 'flags', 'username', 'chname'])

    def __init__(self, recs):
        self.recs = recs

    @staticmethod
    def parse(data):
        recs = []
        while data:
            is_active, channel_id, volume, pan, flags = struct.unpack('<?BHbB', data[:6])
            data = data[6:]
            length = data.find(b'\x00')
            if length == -1:
                raise ValueError
            username = data[:length].decode('utf-8')
            data = data[length + 1:]
            length = data.find(b'\x00')
            if length == -1:
                raise ValueError
            chname = data[:length].decode('utf-8')
            data = data[length + 1:]

            recs.append(ServerUserInfoChangeNotify.UserInfoChange(is_active, channel_id, volume, pan, flags, username, chname))
        return ServerUserInfoChangeNotify(recs)

class ServerConfigChangeNotify(object):
    msgtype = 0x02

    def __init__(self, bpm, bpi):
        self.bpm = bpm
        self.bpi = bpi

    @staticmethod
    def parse(data):
        bpm, bpi = struct.unpack('<HH', data)
        return ServerConfigChangeNotify(bpm, bpi)

class ClientUploadIntervalBegin(object):
    msgtype = 0x83

    FOURCC_OGGV = 0x7647474f

    def __init__(self, guid='\0' * 16, estsize=0, fourcc=FOURCC_OGGV, chidx=0):
        self.guid = guid
        self.estsize = estsize
        self.fourcc = fourcc
        self.chidx = chidx

    def build(self):
        return struct.pack('<16sIIB', self.guid, self.estsize, self.fourcc, self.chidx)

class ClientUploadIntervalWrite(object):
    msgtype = 0x84

    def __init__(self, guid, flags, data):
        self.guid = guid
        self.flags = flags
        self.data = data

    def build(self):
        return struct.pack('<16sB', self.guid, self.flags) + self.data

class ChatMessage(object):
    msgtype = 0xc0

    def __init__(self, parms):
        self.parms = parms

    @staticmethod
    def parse(data):
        parms = [s.decode('utf-8') for s in data.split(b'\0')]
        return ChatMessage(parms)

class KeepAliveMessage(object):
    msgtype = 0xfd

    def build(self):
        return b''

    @staticmethod
    def parse(data):
        return KeepAliveMessage()

def buildMessage(msg):
    data = msg.build()
    return struct.pack('<BI', msg.msgtype, len(data)) + data

class JammrProtocol(protocol.Protocol):
    message_types = {msg.msgtype: msg for msg in (ServerAuthChallengeRequest, ClientAuthUser,
        ServerAuthReply, ServerUserInfoChangeNotify, ServerConfigChangeNotify, ChatMessage,
        KeepAliveMessage)}

    def __init__(self):
        self.buf = b''
        self.keepalive = 3 # seconds
        self.localChannels = []

    def setKeepAlive(self, keepalive):
        if keepalive == 0:
            self.keepalive = 3
        else:
            self.keepalive = keepalive
        self.sendKeepAliveDelayedCall.delay(self.keepalive)
        self.recvKeepAliveDelayedCall.delay(self.keepalive * 3)

    def connectionMade(self):
        self.sendKeepAliveDelayedCall = reactor.callLater(self.keepalive, self.sendKeepAliveTimeout)
        self.recvKeepAliveDelayedCall = reactor.callLater(self.keepalive * 3, self.recvKeepAliveTimeout)

    def connectionLost(self, reason=protocol.connectionDone):
        self.sendKeepAliveDelayedCall.cancel()
        del self.sendKeepAliveDelayedCall
        self.recvKeepAliveDelayedCall.cancel()
        del self.recvKeepAliveDelayedCall

    def sendKeepAliveTimeout(self):
        self.sendKeepAliveDelayedCall = reactor.callLater(self.keepalive, self.sendKeepAliveTimeout)
        self.sendMessage(KeepAliveMessage())

    def recvKeepAliveTimeout(self):
        log.msg('keepalive exceeded without messages from server')
        self.transport.loseConnection()

    def parseMessage(self, data):
        if len(data) < 5:
            return None, 0
        msgtype, length = struct.unpack('<BI', data[:5])
        data = data[5:]
        if len(data) < length:
            return None, 0
        data = data[:length]
        if msgtype not in JammrProtocol.message_types:
            raise InvalidMessageType(msgtype=msgtype)
        return JammrProtocol.message_types[msgtype].parse(data), 5 + length

    def sendMessage(self, msg):
        self.transport.write(buildMessage(msg))

    def dataReceived(self, data):
        self.recvKeepAliveDelayedCall.delay(self.keepalive * 3)
        self.buf += data

        while self.buf:
            try:
                msg, length = self.parseMessage(self.buf)
            except InvalidMessageType:
                log.err()
                self.transport.loseConnection()
                return
            self.buf = self.buf[length:]

            if not msg:
                return

            if msg.msgtype == ServerAuthChallengeRequest.msgtype:
                self.serverAuthChallenge(msg)
            elif msg.msgtype == ServerAuthReply.msgtype:
                self.serverAuthReply(msg)
            elif msg.msgtype == ServerUserInfoChangeNotify.msgtype:
                self.serverUserInfoChangeNotify(msg)
            elif msg.msgtype == ServerConfigChangeNotify.msgtype:
                self.serverConfigChangeNotify(msg)
            elif msg.msgtype == ChatMessage.msgtype:
                self.chatMessage(msg)
            elif msg.msgtype == KeepAliveMessage.msgtype:
                self.keepAliveMessage(msg)

    def serverAuthChallenge(self, msg):
        keepalive = (msg.server_caps >> 8) & 0xff
        self.setKeepAlive(keepalive)

        username = self.factory.username.encode('utf-8')
        password = self.factory.password.encode('utf-8')
        digest = sha1(username + b':' + password).digest()
        passhash = sha1(digest + msg.challenge).digest()
        msg = ClientAuthUser(passhash, self.factory.username,
                             ClientAuthUser.CAPS_ACCEPT_LICENSE,
                             ClientAuthUser.CLIENT_VERSION)
        self.sendMessage(msg)

    def serverAuthReply(self, msg):
        if (msg.flag & 1) == 0:
            self.transport.loseConnection()
            log.msg('authentication failed: %s' % msg.errmsg)
            return
        if self.localChannels:
            self.sendMessage(ClientSetChannelInfo(self.localChannels))
        self.loggedIn()

    def loggedIn(self):
        pass

    def serverUserInfoChangeNotify(self, msg):
        pass

    def serverConfigChangeNotify(self, msg):
        pass

    def chatMessage(self, msg):
        pass

    def keepAliveMessage(self, msg):
        pass
