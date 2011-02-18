import redis
import random
import time
from listen import TEST_PORT

REDIS_DB = 0 # hardcoded

if __name__ == "__main__":
    #try:
        r = redis.Redis(host='localhost', port=TEST_PORT, db=REDIS_DB, password='foobared')
        print 'connected'
        res = r.get('z')
        print res
        r.set('z', str(random.randint(0, 255)))
        print 'set'
        res = r.get('z')
        print 'got: ', res
        r.connection.disconnect()
    #except redis.exceptions.ConnectionError:
        #print 'socket closed at: ',time.time()
