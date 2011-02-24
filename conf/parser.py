#! -*- coding: utf-8 -*-

class ConfigParser(object):

    def __init__(self, *args, **kwargs):
        from config import REDIS_HOST, REDIS_PORT, REDIS_DB, DEFAULT_PERMISSIONS, USER_PERMISSIONS, PORT, TEST_PORT
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
        global_commands = set(default['commands_accepted']).difference(set(default['commands_denied']))
        global_keys = set(default['keys'])
        for user in users.keys():
            # user commands permissions
            accepted_commands = set(users[user]['commands']['accept'])
            excluded_commands = set(users[user]['commands']['exclude'])
            user_can_do = accepted_commands.union(global_commands).symmetric_difference(excluded_commands)
            self.USER_COMMANDS[user] = user_can_do
            # user keys permissions
            accepted_keys = set(users[user]['keys'])
            user_can_do_something_with = accepted_keys.union(global_keys)
            self.USER_KEYS[user] = user_can_do_something_with
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

