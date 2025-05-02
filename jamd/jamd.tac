# Copyright 2012 Stefan Hajnoczi <stefanha@gmail.com>

import json
import twisted.internet.error
from twisted.application import internet, service
from twisted.internet import reactor, protocol, defer
from twisted.python import log
import txredisapi
import settings
import jam

# Create public jams
# Create private jams
# Destroy public/private jams after inactivity
# Perform status update on each running jam periodically

class JamdService(service.Service):
    def __init__(self):
        self.jams = []
        self.redis = None

        # The 'blpop' command blocks the connection so we need a dedicated
        # Redis client connection for this blocking command.
        self.redisForBpop = None
        self.bpopDeferred = None

        self.delayedKickJamCreationCall = None

    def startService(self):
        service.Service.startService(self)

        # Establish 2 connections
        txredisapi.Connection(settings.redis_addr[0], settings.redis_addr[1]).addCallback(self.redisConnected)
        txredisapi.Connection(settings.redis_addr[0], settings.redis_addr[1]).addCallback(self.redisConnected)

    def redisConnected(self, redis):
        if self.redis is None:
            log.msg('Redis connection succeeded')
            self.redis = redis

            # Clear out any stale values
            redis.set('num_public_users', 0)
        elif self.redisForBpop is None:
            log.msg('Bpop Redis connection succeeded')
            self.redisForBpop = redis
            self.kickJamCreation()
        else:
            log.msg('Unexpected redis connection')

    def getRedis(self):
        """Accessor for redis instance so we can change or reconnect behind the scenes"""
        return self.redis

    @defer.inlineCallbacks
    def stopService(self):
        for j in self.jams:
            j.stopService()
        if self.delayedKickJamCreationCall is not None:
            self.delayedKickJamCreationCall.cancel()
            self.delayedKickJamCreationCall = None
        if self.redis is not None:
            r = self.redis
            self.redis = None
            yield r.disconnect()
        if self.redisForBpop is not None:
            r = self.redisForBpop
            self.redisForBpop = None
            yield r.disconnect()
        result = yield service.Service.stopService(self)
        defer.returnValue(result)

    def kickJamCreation(self):
        if self.delayedKickJamCreationCall is not None:
            if self.delayedKickJamCreationCall.active():
                self.delayedKickJamCreationCall.cancel()
            self.delayedKickJamCreationCall = None

        if len(self.jams) >= settings.max_jams:
            return

        self.spawnEmptyPublicJams()

        # Check again since public jams may have been created
        if len(self.jams) >= settings.max_jams:
            return

        if self.bpopDeferred is None:
            self.bpopDeferred = self.redisForBpop.blpop(['create_jam']).addCallback(self.handleCommand).addErrback(self.bpopErrback)

    def countEmptyPublicJams(self):
        return sum(int(j.isPublic() and j.isEmpty()) for j in self.jams)

    def spawnEmptyPublicJams(self):
        empty_public_jams = self.countEmptyPublicJams()
        while empty_public_jams < settings.empty_public_jams:
            self.createJam(settings.default_public_jam_topic)
            empty_public_jams += 1

    def handleCommand(self, bpop_arg):
        queue, data = bpop_arg
        self.bpopDeferred = None

        assert queue == 'create_jam' # the only queue we listen on
        try:
            info = json.loads(data)
        except ValueError:
            log.msg('Failed to parse create_jam JSON: ' + data)
            return
        for k in 'topic', 'acl', 'response_id', 'owner':
            if k not in info:
                log.msg('Missing create_jam JSON "%s" item: %s' % (k, data))
                return

        # Set ACL before spawning jam so there is no race condition when
        # clients can connect before the ACL exists.
        port = self.nextFreePort()
        server = '%s:%s' % (settings.hostname, port)
        self.getRedis().set('acls/%s' % server, info['acl'])

        self.createJam(info['topic'], owner=info['owner'], port=port)

        # This reply is asynchronous, wahjamsrv may not be reachable yet
        response_key = 'create_jam_responses/%s' % info['response_id']
        self.getRedis().rpush(response_key, json.dumps(dict(server=server)))

        # In case caller has gone away, delete the response after some time
        self.getRedis().expire(response_key, 120)

        self.kickJamCreation()

    def nextFreePort(self):
        i = settings.base_port
        while i in (j.port for j in self.jams):
            i += 1
        return i

    def bpopErrback(self, failure):
        self.bpopDeferred = None
        if self.redisForBpop is None:
            pass # ignore connection lost error on shutdown
        else:
            log.err(failure)

    def createJam(self, topic, owner=None, port=None):
        if port is None:
            port = self.nextFreePort()
        j = jam.Jam(port, topic, self, owner=owner)
        self.jams.append(j)
        j.startService()

    def destroyJam(self, j):
        j.stopService()
        self.jams.remove(j)

        # Throttle jam session creation in case they are dying due to
        # wahjamsrv crashes.
        if self.delayedKickJamCreationCall is None:
            self.delayedKickJamCreationCall = reactor.callLater(2, self.kickJamCreation)

    def shouldDestroyIdleJam(self, j):
        """Return True if an idle jam should be destroyed"""
        if j.isPublic():
            return self.countEmptyPublicJams() > settings.empty_public_jams
        else:
            return True

    def firstUserJoined(self, j):
        """Callback when a user joins an empty jam"""
        self.kickJamCreation()

application = service.Application("jamd")
jamdService = JamdService()
jamdService.setServiceParent(application)
