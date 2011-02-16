import sys
import os

cwd = os.getcwd()
sys.path.append('/'.join(cwd.split('/')[:-2]))

from rpac.protocol import ConfigParser

if __name__ == "__main__":
    config = ConfigParser()
    print 'redis_host: ', config.REDIS_HOST
    print 'redis_port: ', config.REDIS_PORT
    print 'proxy port: ', config.PORT
    print 'proxy test port: ', config.TEST_PORT
    print 'user_commands: ', config.USER_COMMANDS
    print 'user_keys: ', config.USER_KEYS
