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
            config['user'] = self.USER_PASSWORDS[password]
            config['password'] = password
            config['commands'] = self.USER_COMMANDS[user]
            config['keys'] = self.USER_KEYS[user]
        except KeyError:
            pass
        return config


class RedisAuthProxy(LineOnlyReceiver):

    def __init__(self, *args, **kwargs):
        self.delimiter = '\r\n' # explicitly
        self.args = [] # arguments for current command
        self.ready = True # ready to parse next command
        self.authorized = False # is authorized
        self.config = ConfigParser()
        self.SINGLE_LINE_RESPONSE = ['PING', ' SET', ' SELECT', ' SAVE', ' BGSAVE', ' SHUTDOWN', ' RENAME', ' LPUSH', ' RPUSH', ' LSET', ' LTRIM']

    def connectionMade(self):
        print 'connection established'

    def lineReceived(self, line):
        """
            Socket input parsing via redis network protocol
        """
        print 'line: ', line
        if self.ready and line.startswith('*'):
            self.arguments_number = int(line[1:])-1
            self.get_command = True
            self.ready = False

        elif self.get_command and not line.startswith('$'):
            self.command = line
            if not self.authorized and self.command != 'AUTH':
                self.sendLine('-NOTAUTHORIZED')
            self.get_command = False

        elif not self.get_command and self.arguments_number and not self.ready:
            self.args.append(line)
            self.arguments_number -= 1
            if self.authorized:
                self.proxy_execute(command, args)
                self.ready = True
                self.args = []
            else:
                # first command - authorization
                print 'self.args: ', self.args
                password = self.args[-1]
                self.authClient(password)

        else:
            raise self.WrongCommand


    def authClient(self, password):
        """
            Authorization procedure
        """
        print 'password: ', password
        self.userconfig = self.config.getConfigByPassword(password)
        if self.userconfig:
            self.sendLine('+OK')
        else:
            self.sendLine('-AUTHERROR')

    def proxyExecute(self, command, args):
        """
            Command execution via python redis_client and sending results back to proxy client.
        """
        raise NotImplemented

    class RedisError(Exception):
        pass

    class WrongCommand(RedisError):
        pass
