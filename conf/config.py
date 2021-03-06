# host used for connectino to redis server
REDIS_HOST = '127.0.0.1'
# port used for connection to redis server
REDIS_PORT = 6379
# redis db
REDIS_DB = 0
# test proxy host
TEST_HOST = '127.0.0.1'
# port used by run.py and client.py test scripts
TEST_PORT = 8910
# port used start script
PORT = 8910
# permissions - commands and keys accepted for all users, unless stated otherwise in USERS section
DEFAULT_PERMISSIONS = {
            'commands_accepted':
                    ['PING', 'SELECT', 'ZADD', 'QUIT'],
            'commands_denied':
                    ['MULTI', 'EXEC', 'DISCARD', 'WATCH', 'UNWATCH', 'FLUSHDB', 'FLUSHALL', 'INFO', 'MONITOR', 'SLAVEOF', 'CONFIG'],
            'exact_keys':
                    ['keyA', 'keyB', 'TEST'],
            'startswith_keys':
                    ['public::'],
          }
# permissions per user - make additions to DEFAULT and overrides it if needed
USER_PERMISSIONS = {
            'userA':
                {
                    'commands':
                        {
                            'accept': ['GET','SET', 'LPUSH'],
                            'exclude': ['ZADD'],
                        },
                    'exact_keys': [],
                    'startswith_keys': [],
                    'password': 'foobared' # password must be unique for each client - probably i should fix it
                },

            'TestUser': #special user for testing purposes
                {
                    'commands':
                        {
                            'accept': ['GET','SET', 'LPUSH', 'RPOP'],
                            'exclude': ['ZADD']
                        },
                    'exact_keys': ['TESTLIST', 'TEST_KEY', 'TEST_KEY_2'],
                    'startswith_keys': ['TestUser::'],
                    'password': 'testbared'
                }
        }
