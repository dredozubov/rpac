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
        exact_global_keys = set(default['exact_keys'])
        startswith_global_keys = set(default['startswith_keys'])
        for user in users.keys():
            # user commands permissions
            accepted_commands = set(users[user]['commands']['accept'])
            excluded_commands = set(users[user]['commands']['exclude'])
            user_can_do = accepted_commands.union(global_commands).symmetric_difference(excluded_commands)
            self.USER_COMMANDS[user] = user_can_do
            # user keys permissions
            exact_accepted_keys = set(users[user]['exact_keys'])
            startswith_accepted_keys = set(users[user]['startswith_keys'])
            user_can_do_something_with = {}
            user_can_do_something_with['exact'] = exact_accepted_keys.union(exact_global_keys)
            user_can_do_something_with['startswith'] = startswith_accepted_keys.union(startswith_global_keys)
            self.USER_KEYS[user] = user_can_do_something_with
            # user passwords
            self.USER_PASSWORDS[users[user]['password']] = user # keys are passwords

    def getConfigByPassword(self, password):
        config = {}
        try:
            config['user'] = user = self.USER_PASSWORDS[password]
            config['password'] = password
            config['commands'] = self.USER_COMMANDS[user]
            config['exact_keys'] = self.USER_KEYS[user]['exact']
            config['startswith_keys'] = self.USER_KEYS[user]['startswith']
        except KeyError:
            pass
        return config

