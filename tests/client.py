import redis
from run import TEST_PORT

TEST_DB = 3

if __name__ == "__main__":
    r = redis.Redis(host='localhost', port=TEST_PORT, db=TEST_DB, password='foobared')
    print 'connected'
    r.ping()
    print 'pinged'
