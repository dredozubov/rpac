# host used for connectino to redis server
REDIS_HOST = '127.0.0.1'
# port used for connection to redis server
REDIS_PORT = 6379
# port used by run.py and client.py test scripts
TEST_PORT = 8910
# port used start script
PORT = 8910
# permissions - commands and keys accepted for all users, unless stated otherwise in USERS section
DEFAULT_PERMISSIONS = {
            'commands':
                    ['PING'],
            'keys':
                    ['keyA', 'keyB']
          }
# permissions per user - make additions to DEFAULT and overrides it if needed
USER_PERMISSIONS = {
            'userA':
                {
                    'commands':
                        {
                            'accept': ['GET','SET'],
                            'exclude': ['PING']
                        },
                    'keys':
                        [],
                    'password': 'foobared' # password must be unique for each client - probably i should fix it
                }
        }
