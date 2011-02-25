#! -*- coding: utf-8 -*-
import redis
import random
import time
from listen import TEST_HOST, TEST_PORT
from itertools import izip

# hardcoded
REDIS_DB = 0
VALID_PASSWORD = 'testbared'
INVALID_PASSWORD = 'TinaFey'
VALID_COMMANDS = [
                    'SET TEST VALUE',
                    'GET TEST',
                    'PING',
                    u'LPUSH TESTLIST значение',
                 ]

INVALID_COMMANDS = [
                        'LPOP TESTLIST',
                        'RPUSH TESTLIST VALUE',
                   ]

VALID_KEYS = [
                'TEST_KEY',
                'TEST_KEY_2',
                'TestUser::foo'
             ]

INVALID_KEYS = [
                'INVALID_TEST_KEY',
                'INVALID_TEST_KEY_2',
             ]


def auth_valid_routine(host, port, password):
    try:
        r = redis.Redis(host=TEST_HOST, port=TEST_PORT, db=REDIS_DB, password=password)
        r.ping()
    except Exception, ex:
        VALID_AUTH_ERRORS['text'].append(ex)
        VALID_AUTH_ERRORS['number'] += 1
    finally:
        r.connection.disconnect()

def auth_invalid_routine(host, port, password):
    try:
        r = redis.Redis(host=TEST_HOST, port=TEST_PORT, db=REDIS_DB, password=password)
        r.ping()
        INVALID_AUTH_ERRORS['text'].append('password \'%s\' should not be authorized' % password)
        INVALID_AUTH_ERRORS['number'] += 1
    except Exception, ex:
        pass
    r.connection.disconnect()

def commands_valid_routine(host, port, password, commands):
    try:
        r = redis.Redis(host=TEST_HOST, port=TEST_PORT, db=REDIS_DB, password=password)
        for command in commands:
            r.execute_command(*command.split(' '))
    except Exception, ex:
        VALID_COMMANDS_ERRORS['text'].append(ex)
        VALID_COMMANDS_ERRORS['number'] += 1
    finally:
        r.connection.disconnect()

def commands_invalid_routine(host, port, password, commands):
    r = redis.Redis(host=TEST_HOST, port=TEST_PORT, db=REDIS_DB, password=password)
    for command in commands:
        try:
            res = r.execute_command(*command.split(' '))
            INVALID_COMMANDS_ERRORS['text'].append(str(command)+' should not be executed')
            INVALID_COMMANDS_ERRORS['number'] += 1
        except Exception, ex:
            pass
    r.connection.disconnect()

def keys_valid_routine(host, port, password, keys):
    try:
        r = redis.Redis(host=TEST_HOST, port=TEST_PORT, db=REDIS_DB, password=password)
        map(lambda x: r.lpush(x, 'value'), keys)
        map(lambda x: r.rpop(x), keys)
    except Exception, ex:
        VALID_KEYS_ERRORS['text'].append(ex)
        VALID_KEYS_ERRORS['number'] += 1
    finally:
        r.connection.disconnect()

def keys_invalid_routine(host, port, password, keys):
    r = redis.Redis(host=TEST_HOST, port=TEST_PORT, db=REDIS_DB, password=password)
    for key in keys:
        try:
            r.lpush(key, 'value')
            INVALID_KEYS_ERRORS['text'].append('key %s should not be authorized' % key)
            INVALID_KEYS_ERRORS['number'] += 1
        except Exception, ex:
            pass
    r.connection.disconnect()

def report(counter, title):
    print '%s Errors Number: ' % title, counter['number']
    if counter['number']:
        print '%s Errors Messages: ' % title
        for i in ['%s: %s' % x for x in enumerate(counter['text'], 1)]:
            print i
    print '\n'

def __run_tests(number_of_tries=1):
    auth_valid_routine(TEST_HOST, TEST_PORT, VALID_PASSWORD)
    auth_invalid_routine(TEST_HOST, TEST_PORT, INVALID_PASSWORD)
    if VALID_AUTH_ERRORS['number']:
        import sys
        print 'No need to continue, can\'t authorize user with password %s' % VALID_PASSWORD
        sys.exit()
    for x in xrange(number_of_tries):
        commands_valid_routine(TEST_HOST, TEST_PORT, VALID_PASSWORD, VALID_COMMANDS)
    for x in xrange(number_of_tries):
        commands_invalid_routine(TEST_HOST, TEST_PORT, VALID_PASSWORD, INVALID_COMMANDS)
    for x in xrange(number_of_tries):
        keys_valid_routine(TEST_HOST, TEST_PORT, VALID_PASSWORD, VALID_KEYS)
    for x in xrange(number_of_tries):
        keys_invalid_routine(TEST_HOST, TEST_PORT, VALID_PASSWORD, INVALID_KEYS)

def run_suite():

    MESSAGES = [
                    VALID_AUTH_ERRORS,
                    INVALID_AUTH_ERRORS,
                    VALID_COMMANDS_ERRORS,
                    INVALID_COMMANDS_ERRORS,
                    VALID_KEYS_ERRORS,
                    INVALID_KEYS_ERRORS
               ]

    MESSAGES_TITLES = [
                    'Valid Auth',
                    'Invalid Auth',
                    'Valid Commands',
                    'Invalid Commands',
                    'Valid Keys',
                    'Invalid Keys',
               ]

    ERRORS = sum(x['number'] for x in MESSAGES)

    __run_tests()

    print 'Total Errors: ', ERRORS, '\n'
    map(lambda x: report(x[0], x[1]), izip(MESSAGES, MESSAGES_TITLES))


if __name__ == "__main__":
    VALID_AUTH_ERRORS = {'number': 0, 'text': []}
    INVALID_AUTH_ERRORS = {'number': 0, 'text': []}
    VALID_COMMANDS_ERRORS = {'number': 0, 'text': []}
    INVALID_COMMANDS_ERRORS = {'number': 0, 'text': []}
    VALID_KEYS_ERRORS = {'number': 0, 'text': []}
    INVALID_KEYS_ERRORS = {'number': 0, 'text': []}
    run_suite()
