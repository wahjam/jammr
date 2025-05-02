#!/usr/bin/python3
# Copyright 2013-2021 Stefan Hajnoczi <stefanha@gmail.com>

import sys
import argparse
import base64
import http.client
import random
import urllib.request, urllib.parse, urllib.error
import uuid
import ssl
from twisted.internet import reactor, protocol
from twisted.python import log
from twisted.protocols.basic import FileSender
from song import Song
from protocol import JammrProtocol, ClientSetChannelInfo, ClientUploadIntervalBegin, ClientUploadIntervalWrite, buildMessage

JAMMR_API_URL = 'https://jammr.net/api/'
SSL_VERIFY = False # development servers have self-signed certificates

def jammr_api_call(url, username, password, post_data=None):
    '''Make a REST API call and return (status_code, response_body)'''
    data = None
    if post_data is not None:
        data = urllib.parse.urlencode(post_data, 1).encode('utf-8')

    auth = 'Basic ' + base64.b64encode(username.encode('utf-8') + b':' + password.encode('utf-8')).decode('utf-8').strip()

    req = urllib.request.Request(JAMMR_API_URL + url, data, {'Authorization': auth})

    ctx = ssl.create_default_context()
    if not SSL_VERIFY:
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

    try:
        resp = urllib.request.urlopen(req, context=ctx)
    except urllib.error.URLError:
        raise

    return resp.getcode(), resp.read().decode('utf-8')

def jammr_api_set_token(username, password):
    '''Set the user's authentication token via the REST API and return it'''
    log.msg(f'Setting jammr authentication token for user "{username}"...')
    token = random.randbytes(20).hex()
    http_code, _ = jammr_api_call('tokens/{}/'.format(username),
                                  username,
                                  password,
                                  post_data={'token': token})
    if http_code != http.client.CREATED:
        log.msg(f'Failed to set authentication token (HTTP code {http_code})')
        sys.exit(1)
    log.msg('Ok')
    return token

class UploadTransform(object):
    '''Wrap audio data in protocol headers'''
    def __init__(self, size):
        self.size = size
        self.consumed = 0

    def __call__(self, data):
        output = []
        if not hasattr(self, 'guid'):
            self.guid = uuid.uuid4().bytes
            msg = ClientUploadIntervalBegin(guid=self.guid)
            output.append(buildMessage(msg))
        flags = 0
        self.consumed += len(data)
        if self.consumed >= self.size:
            flags = 1
        msg = ClientUploadIntervalWrite(self.guid, flags, data)
        output.append(buildMessage(msg))
        return b''.join(output)

class BotClient(JammrProtocol):
    def __init__(self):
        JammrProtocol.__init__(self)

    def connectionMade(self):
        JammrProtocol.connectionMade(self)
        for trackname in self.factory.song.tracks:
            ch = ClientSetChannelInfo.ChannelInfo(trackname, 0, 0, 0)
            self.localChannels.append(ch)

    def connectionLost(self, reason):
        if hasattr(self, 'intervalDelayedCall'):
            self.intervalDelayedCall.cancel()
            del self.intervalDelayedCall
        JammrProtocol.connectionLost(self, reason)

    def loggedIn(self):
        self.intervalBegin()

    def intervalBegin(self):
        tracks = self.factory.song.tracks
        for trackname, intervals in tracks.items():
            filename = random.choice(intervals)
            if filename is None:
                log.msg('beginning silent interval on track %s' % trackname)
                self.sendMessage(ClientUploadIntervalBegin(fourcc=0))
            else:
                fobj = open(filename, 'rb')
                fobj.seek(0, 2)
                size = fobj.tell()
                fobj.seek(0, 0)
                log.msg('beginning file transfer for %s on track %s' % (filename, trackname))
                sender = FileSender()
                sender.CHUNK_SIZE = 9 * 1024
                sender.beginFileTransfer(fobj, self.transport, UploadTransform(size))
        # TODO should really set bpm/bpi at beginning of connection and then just use the server's bpm/bpi value for interval duration (not all jam descriptions may include tempo information)
        intervalDuration = self.factory.song.bpi * 60 / self.factory.song.bpm
        self.intervalDelayedCall = reactor.callLater(intervalDuration, self.intervalBegin)

class BotFactory(protocol.ClientFactory):
    protocol = BotClient

    def __init__(self, username, password, song):
        self.username = username
        self.password = password
        self.song = song

    def clientConnectionLost(self, connector, reason):
        reactor.stop()

def main(args):
    parser = argparse.ArgumentParser(description='Automated jammr client')
    parser.add_argument('--host', default='127.0.0.1', help='host to connect to')
    parser.add_argument('--port', default=2049, type=int, help='TCP port number to connect to')
    parser.add_argument('username', help='account username')
    parser.add_argument('password', help='account password')
    parser.add_argument('song', help='song JSON file')
    args = parser.parse_args()

    log.startLogging(sys.stderr)

    song = Song.loadJSON(open(args.song, 'rt').read())

    token = jammr_api_set_token(args.username, args.password)

    log.startLogging(sys.stderr)
    f = BotFactory(args.username, token, song)
    reactor.connectTCP(args.host, args.port, f)
    reactor.run()

if __name__ == '__main__':
    main(sys.argv)
