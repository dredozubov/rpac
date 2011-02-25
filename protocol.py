#! -*- coding: utf-8 -*-
from twisted.protocols.basic import LineOnlyReceiver
from twisted.internet.tcp import Server
from twisted.internet import abstract
from redis import Redis, ResponseError, ConnectionError
from rpac.conf.parser import ConfigParser
import time
import re
import logging


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
            length = int(response)
            if length == -1:
                return None
            if not catch_errors:
                print 'errors'
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
                return byte+data

        return byte+response



class RedisAuthProxy(LineOnlyReceiver):
    """
        Twisted Protocol class
    """

    def __init__(self, *args, **kwargs):
        self.delimiter = str('\r\n') # explicitly
        self.args = [] # arguments for current command
        self.ready = True # ready to parse next command
        self.authorized = False # is authorized
        self.config = ConfigParser()
        self.command = '' # internal command buffer
        self.re_arg = re.compile('^\*(\d)')
        #self.SINGLE_LINE_RESPONSE = ['PING', ' SET', ' SELECT', ' SAVE', ' BGSAVE', ' SHUTDOWN', ' RENAME', ' LPUSH', ' RPUSH', ' LSET', ' LTRIM']
        #self.NOT_RECV_COMMANDS = ['SUBSCRIBE', 'UNSUBSCRIBE', 'PSUBSCRIBE', 'PUNSUBSCRIBE']
        self.BLOCKING_COMMANDS = ['BLPOP', 'BRPOP', 'SMOVE']
        self.ALL_KEYS_COMMANDS = ['DEL', 'MGET', 'SINTER', 'SINTERSTORE', 'SUNION', 'SUNIONSTORE', 'SDIFF', 'SDIFFSTORE', 'RENAME', 'RENAMENX']
        self.KEYLESS_COMMANDS = ['PING', 'DBSIZE', 'SELECT', 'FLUSHDB', 'FLUSHALL', 'AUTH']

    def resetCommandBuffer(self):
        self.command = u''

    def connectToRedis(self):
        # client is connected to proxy, time to connect to redis itself
        self.redis = RedisProxy(host=self.config.REDIS_HOST, port=self.config.REDIS_PORT, db=self.config.REDIS_DB)
        from time import gmtime
        self.redis.lpush('time', str(gmtime()))

    def checkCommand(self, command):
        if command.upper() in self.config.USER_COMMANDS[self.userconfig['user']]:
            return True
        else:
            return

    def __checkKeys(self, arguments):
        exact_restricted_keys = []
        startswith_restricted_keys = []
        for argument in arguments:

            namespaced = False
            for skey in self.userconfig['startswith_keys']:
                if argument.startswith(skey):
                    namespaced = True
            if not namespaced:
                startswith_restricted_keys.append(argument)

            if argument not in self.userconfig['exact_keys']:
                exact_restricted_keys.append(argument)

        restricted = set(startswith_restricted_keys).intersection(set(exact_restricted_keys))
        return restricted

    def checkKeys(self, command, arguments):
        checked = None
        if command in ['MSET', 'MSETNX']:
            # our main interest is arguments with odd indexes
            restricted_keys = self.__checkKeys(arguments[::2])
        elif command in self.ALL_KEYS_COMMANDS:
            # we must check all arguments
            restricted_keys = self.__checkKeys(arguments)
        else:
            restricted_keys = self.__checkKeys([arguments[0]])
        return restricted_keys

    def checkPermissions(self, command_list):
        command = command_list[0]
        arguments = command_list[1:]
        if self.checkCommand(command):
            if command not in self.KEYLESS_COMMANDS:
                restricted_keys = self.checkKeys(command, arguments)
            else:
                restricted_keys = []
            if not restricted_keys:
                print 'proxyExecute(command): ', command_list
                self.proxyExecute(command_list)
            else:
                self.sendLine('-ERR restricted keys: %s' % ' '.join(restricted_keys))
        elif command in self.BLOCKING_COMMANDS:
            # in case it'll be removed in config.py
            self.sendLine('-ERR blocking commands restricted: %s' % command.upper())
        else:
            self.sendLine('-ERR restricted command: %s' % command.upper())

    def sendLine(self, line):
        if not line:
            line = '$-1'
        if type(line) == 'unicode':
            line = self.safe_unicode(line).encode('utf-8')
        abstract.FileDescriptor.write(self.transport, str(line.rstrip('\r\n')+self.delimiter))

    def sendTerminate(self):
        abstract.FileDescriptor.write(self.transport, self.delimiter)

    def lineReceived(self, line):
        """
            Socket input parsing via redis network protocol
        """
        self.command += line+'\r\n'
        args = self.re_arg.match(self.command)
        if args:
            repeats = int(args.groups()[0])-1
            # DL for delimiter
            acceptable_range = u'\wАБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЬЭЮЯабвгдеёжзийклмнопрстуфхцчшщъьэюя:punct:'
            arg_repeats = unicode('\$\d+DL(['+acceptable_range+']+)DL')*repeats
            re_val = unicode('^\*\dDL\$\d+DL([a-zA-Z:punct:]+)DL'+arg_repeats).replace('DL', '\r\n').encode('utf-8')
            regex = re.compile(re_val) # can't replicate effect of acceptable_range with re.U, dunno why
            m = regex.match(self.command)
            if m:
                self.command = self.command[m.end():]
                matches = [c for c in m.groups() if c is not None]
                # twisted breaks while sending unicode, so..
                command = matches[0].encode('utf-8')
                if len(matches) > 1:
                    arguments = list(matches[1:])
                else:
                    arguments = None

                # printing
                if arguments:
                    print '%s %s' % (command, ' '.join(arguments))
                elif command:
                    print command

                if command in ['AUTH', 'auth'] and not self.authorized:
                    # authorization
                    password = arguments[0]
                    self.authClient(password)
                elif self.authorized:
                    self.checkPermissions(m.groups())
                else:
                    self.sendLine('-ERR authorization denied')

    def authClient(self, password):
        """
            Authorization procedure
        """
        self.userconfig = self.config.getConfigByPassword(password)
        print self.userconfig
        # if self.userconfig exists - user exists
        if self.userconfig:
            self.sendLine('+OK')
            self.authorized = True
            self.connectToRedis()
            print 'authorized!'
        else:
            self.sendLine('-ERR invalid password')
            print 'not authorized!'

    def proxyExecute(self, command):
        """
            Command execution via RedisProxy and sending results back to client.
        """
        self.redis.execute_command(*command)
        # this condition must include non-recv commands support etc
        if hasattr(self.redis, 'res_data'):
            self.sendLine(self.redis.res_data)
        else:
            self.sendLine('-ERR wrong command')

    class RedisError(Exception):
        pass

    class AuthError(RedisError):
        pass
