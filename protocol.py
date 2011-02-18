#! -*- coding: utf-8 -*-
from twisted.protocols.basic import LineOnlyReceiver
from twisted.internet.tcp import Server
from twisted.internet import abstract
from redis import Redis, ResponseError, ConnectionError
import time
import re
import logging

class ConfigParser(object):

    def __init__(self, *args, **kwargs):
        from rpac.conf.config import REDIS_HOST, REDIS_PORT, REDIS_DB, DEFAULT_PERMISSIONS, USER_PERMISSIONS, PORT, TEST_PORT
        self.REDIS_HOST = REDIS_HOST
        self.REDIS_PORT = REDIS_PORT
        self.REDIS_DB = REDIS_DB
        self.TEST_PORT = TEST_PORT
        self.PORT = PORT
        self.USER_COMMANDS = {}
        self.USER_KEYS = {}
        self.USER_PASSWORDS = {}
        self.__calculate_permissions(USER_PERMISSIONS, DEFAULT_PERMISSIONS)

    def __calculate_permissions(self, users, default):
        global_commands = set(default['commands'])
        global_keys = set(default['keys'])
        for user in users.keys():
            # user commands permissions
            accepted_commands = set(users[user]['commands']['accept'])
            excluded_commands = set(users[user]['commands']['exclude'])
            user_can_do = accepted_commands.union(global_commands).symmetric_difference(excluded_commands)
            self.USER_COMMANDS[user] = user_can_do
            # user keys permissions
            accepted_keys = set(users[user]['commands']['accept'])
            excluded_keys = set(users[user]['commands']['exclude'])
            user_can_do_with = accepted_keys.union(global_commands).symmetric_difference(excluded_keys)
            self.USER_KEYS[user] = user_can_do
            # user passwords
            self.USER_PASSWORDS[users[user]['password']] = user # keys are passwords

    def getConfigByPassword(self, password):
        config = {}
        try:
            config['user'] = user = self.USER_PASSWORDS[password]
            config['password'] = password
            config['commands'] = self.USER_COMMANDS[user]
            config['keys'] = self.USER_KEYS[user]
        except KeyError:
            pass
        return config


class RedisProxy(Redis):
    """
        Redis client used by RedisAuthProxy
    """

    def parse_response(self, command_name, catch_errors=False, **options):
        response = self._parse_response(command_name, catch_errors)
        self.res_data = response
        print 'self.res_data: ', repr(self.res_data)
        return

    def _parse_response(self, command_name, catch_errors=False):
        conn = self.connection
        response = conn.read()
        if not response:
            self.connection.disconnect()
            self.res_data = "-ERR Socket closed on remote end"

        # server returned a null value
        if response in ('$-1', '*-1'):
            return None

        byte, response = response[0], response[1:]
        # bulk response
        if byte == '$':
            length = int(response)
            if length == -1:
                return None
            response = length and conn.read(length) or ''
            return byte+str(length)+'\r\n'+response

        # multi-bulk response
        if byte == '*':
            print 'multi-bulk'
            length = int(response)
            if length == -1:
                return None
            if not catch_errors:
                return [self._parse_response(command_name, catch_errors) for i in range(length)]
            else:
                # for pipelines, we need to read everything,
                # including response errors. otherwise we'd
                # completely mess up the receive buffer
                data = []
                for i in range(length):
                    try:
                        data.append(
                            self._parse_response(command_name, catch_errors)
                            )
                    except Exception, e:
                        data.append(e)
                print 'returning multi-bulk data'
                return byte+data

        print 'returning byte+response'
        return byte+response



class RedisAuthProxy(LineOnlyReceiver):
    """
        Twisted server class
    """

    def __init__(self, *args, **kwargs):
        self.delimiter = '\r\n' # explicitly
        self.args = [] # arguments for current command
        self.ready = True # ready to parse next command
        self.authorized = False # is authorized
        self.config = ConfigParser()
        self.command = u'' # internal command buffer
        self.re_arg = re.compile('^\*(\d)')
        self.SINGLE_LINE_RESPONSE = ['PING', ' SET', ' SELECT', ' SAVE', ' BGSAVE', ' SHUTDOWN', ' RENAME', ' LPUSH', ' RPUSH', ' LSET', ' LTRIM']
        self.NOT_RECV_COMMANDS = set(['SUBSCRIBE', 'UNSUBSCRIBE', 'PSUBSCRIBE', 'PUNSUBSCRIBE'])

    def resetCommandBuffer(self):
        self.command = u''

    def connectionMade(self):
        # client is connected to proxy, time to connect to redis itself
        self.redis = RedisProxy(host=self.config.REDIS_HOST, port=self.config.REDIS_PORT, db=self.config.REDIS_DB)

    def sendLine(self, line):
        abstract.FileDescriptor.write(self.transport, line+self.delimiter)

    def lineReceived(self, line):
        """
            Socket input parsing via redis network protocol
        """
        self.command += line+'\r\n'
        args = self.re_arg.match(self.command)
        if args:
            repeats = int(args.groups()[0])-1
            # DL for delimiter
            regex = re.compile(str('^\*\dDL\$\d+DL([a-zA-Z]+)DL'+'\$\d+DL(\w+)DL'*repeats).replace('DL', '\r\n'))
            m = regex.match(self.command)
            if m:
                self.command = self.command[m.end():]
                matches = [c for c in m.groups() if c is not None]
                command = unicode(matches[0])

                if len(matches) > 1:
                    arguments = list(matches[1:])
                else:
                    arguments = None

                print 'command: ', command
                print 'arguments: ', arguments

                # printing
                if arguments:
                    print '%s %s' % (command, ' '.join(arguments))
                elif command:
                    print command

                if command == 'AUTH' and not self.authorized:
                    # authorization
                    password = arguments[0]
                    self.authClient(password)
                elif self.authorized:
                    # permissions check
                    if command.upper() in self.config.USER_COMMANDS[self.userconfig['user']]:
                        print 'proxyExecute(command): ', m.groups()
                        self.proxyExecute(m.groups())
                    else:
                        self.sendLine('-ERR restricted command: %s' % command.upper())
                else:
                    self.sendLine('-ERR authorization denied')
                    try:
                        raise self.AuthError
                    finally:
                        self.redis.connection.disconnect()

    def authClient(self, password):
        """
            Authorization procedure
        """
        self.userconfig = self.config.getConfigByPassword(password)
        # if self.userconfig exists - user exists
        if self.userconfig:
            self.sendLine('+OK')
            self.authorized = True
            print 'authorized!'
        else:
            self.sendLine('-ERR authorization denied')
            try:
                raise self.AuthError
            finally:
                self.redis.connection.disconnect()

    def proxyExecute(self, command):
        """
            Command execution via RedisProxy and sending results back to client.
        """
        self.redis.execute_command(*command)
        print 'after execute_command(): ', time.time()
        # this condition must include non-recv commands support etc
        if hasattr(self.redis, 'res_data'):
            self.sendLine(self.redis.res_data)
        else:
            self.sendLine('-ERR wrong command')

    class RedisError(Exception):
        pass

    class WrongCommand(RedisError):
        pass

    class AuthError(RedisError):
        pass
