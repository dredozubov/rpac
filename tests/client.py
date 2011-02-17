import redis
from listen import TEST_PORT

REDIS_DB = 0 # hardcoded

if __name__ == "__main__":
    r = redis.Redis(host='localhost', port=TEST_PORT, db=REDIS_DB, password='foobared')
    print 'connected'
    r.ping()
    print 'pinged'
    r.set('z', str(random.randint(0, 255)))
    print 'set'
    res = r.get('z')
    print 'got: ', res
    r.connection.disconnect()
