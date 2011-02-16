#! -*- coding: utf-8 -*-
from twisted.protocols.basic import LineOnlyReceiver
import re

class ConfigParser(object):

    def __init__(self, *args, **kwargs):
        from rpac.conf.config import REDIS_HOST, REDIS_PORT, DEFAULT_PERMISSIONS, USER_PERMISSIONS, PORT, TEST_PORT
        self.REDIS_HOST = REDIS_HOST
        self.REDIS_PORT = REDIS_PORT
        self.TEST_PORT = TEST_PORT
        self.PORT = PORT
        self.USER_COMMANDS = {}
        self.USER_KEYS = {}
        self.__calculate_permissions(USER_PERMISSIONS, DEFAULT_PERMISSIONS)

    def __calculate_permissions(self, users, default):
        global_commands = set(default['commands'])
        global_keys = set(default['keys'])
        for user in users.keys():
            accepted_commands = set(users[user]['commands']['accept'])
            excluded_commands = set(users[user]['commands']['exclude'])
            user_can_do = accepted_commands.union(global_commands).symmetric_difference(excluded_commands)
            self.USER_COMMANDS[user] = user_can_do
            accepted_keys = set(users[user]['commands']['accept'])
            excluded_keys = set(users[user]['commands']['exclude'])
            user_can_do_with = accepted_keys.union(global_commands).symmetric_difference(excluded_keys)
            self.USER_KEYS[user] = user_can_do


class RedisLineAuth(LineOnlyReceiver):

    def __init__(self, *args, **kwargs):
        self.delimiter = '\r\n' # explicitly
        self.args = [] # arguments for current command
        self.ready = True # ready to parse next command
        self.authorize = False # is authorized

    def connectionMade(self):
        print 'connection established'

    def lineReceived(self, line):
        """
            Socket input parsing via redis network protocol
        """
        if self.ready and line.startswith('*'):
            self.arguments_number = integer(line[1:])-1
            self.get_command = True
            self.ready = False
        else:
            raise self.WrongCommand

        if self.get_command and not line.startswith('$'):
            self.command = line
            if not self.authorized and command != 'AUTH':
                raise AuthError('Must Authorize First!')
            self.get_command = False

        if not self.get_command and self.arguments_number:
            self.args.append(line)
            self.arguments_number -= 1
            if self.authorized:
                self.proxy_execute(command, args)
                self.ready = True
                self.args = []
            else:
                # first command - authorization
                self.authClient()

    def authClient(self, password):
        """
            Authorization procedure
        """
        raise NotImplemented

    def proxyExecute(self, command, args):
        """
            Command execution via python redis_client and sending results back to proxy client.
        """
        raise NotImplemented

    class RedisError(Exception):
        pass

    class WrongCommand(RedisError):
        pass

    class AuthError(RedisError):
        pass
