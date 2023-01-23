import json
import re

from database_manager import DatabaseManager
from user import User


class Response:
    def __init__(self, input_data, server):
        self.input_data = input_data
        self.server = server
        self.data = self.set()

    @property
    def input_data(self):
        return self._input_data

    @input_data.setter
    def input_data(self, value):
        if type(value) == bytes:
            self._input_data = value.decode()
        else:
            self._input_data = value

    @property
    def data(self):
        return self._data

    @data.setter
    def data(self, value):
        self._data = value

    @property
    def as_bytes(self):
        self.data = bytes(self.data, 'utf-8')
        return self

    @property
    def as_json(self):
        self.data = json.dumps(self.data)
        return self

    def set(self):
        command = self.input_data.split()[0]

        match command:
            case 'uptime':
                return f'Server uptime: {round(self.server.uptime, 2)} s'
            case 'help':
                return f'Available commands:\n' \
                       f'"help" - get the commands list\n' \
                       f'"login <username> <password>" - log in to the server\n' \
                       f'"signup <username> <password>" - create new account\n' \
                       f'"users" - list of users on the server, log in first\n' \
                       f'"uptime" - get server lifetime\n' \
                       f'"info" - get server version\n' \
                       f'"stop" - stops both the client and the server\n'
            case 'info':
                return f'Server version: {self.server.version}'
            case 'stop':
                return None
            case 'signup':
                return self.user_signup()
            case 'login':
                return self.user_login()
            case 'users':
                return self.user_list()
        return 'Unknown command'

    def user_signup(self):
        name, pw = self.get_credentials('signup')
        if name and pw:
            user = User(name, pw)
            if user.name in [user.name for user in DatabaseManager.get_users()]:
                return 'This username is already taken.'

            DatabaseManager.add_user(user)
            return f'User created: {user.name}'
        return 'Make sure to provide username and password.'

    def user_login(self):
        name, pw = self.get_credentials('login')
        if name and pw:
            user = User(name, pw)
            if user in DatabaseManager.get_users():
                return 'Logged in.'
            return 'Incorrect credentials.'
        return 'Make sure to provide username and password.'

    def user_list(self):
        name, pw = self.get_credentials('users')
        if name and pw:
            user = User(name, pw)
            if user in DatabaseManager.get_users():
                return User.get_usernames()
            return 'Incorrect credentials.'
        return 'Log in first.'

    def get_credentials(self, command):
        r = re.compile(rf'({command})\s(\S+)\s(\S+)')
        match = r.match(self.input_data)
        if match and len(match.groups()) == 3:
            name = match[2]
            pw = match[3]
            return name, pw
        return None, None
