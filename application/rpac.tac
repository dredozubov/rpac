# You can run this .tac file directly with:
#    twistd -ny service.tac

import sys
import os

cwd = os.getcwd()
sys.path.append('/'.join(cwd.split('/')[:-1]))

"""
This is an example .tac file which starts a webserver on port 8080 and
serves files from the current working directory.

The important part of this, the part that makes it a .tac file, is
the final root-level section, which sets up the object called 'application'
which twistd will look for
"""

from twisted.application import service, internet
from twisted.internet import protocol
from rpac.protocol import RedisAuthProxy
from rpac.conf.config import PORT

def getProxy():
    """
    Return a service suitable for creating an application object.

    This service is a simple web server that serves files on port 8080 from
    underneath the current working directory.
    """
    rpacFactory = protocol.Factory()
    rpacFactory.protocol = RedisAuthProxy

    return internet.TCPServer(PORT, rpacFactory)

# this is the core part of any tac file, the creation of the root-level
# application object
application = service.Application("rpac")

# attach the service to its parent application
service = getProxy()
service.setServiceParent(application)
