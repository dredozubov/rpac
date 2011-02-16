import sys
import os

cwd = os.getcwd()
sys.path.append('/'.join(cwd.split('/')[:-2]))

from twisted.internet import protocol, defer, reactor
from rpac.protocol import RedisAuthProxy
from rpac.conf.rpac import TEST_PORT

if __name__ == '__main__':
    rpacFactory = protocol.Factory()
    rpacFactory.protocol = RedisAuthProxy

    reactor.listenTCP(TEST_PORT, rpacFactory)
    reactor.run()
