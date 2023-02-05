import json
import re

from database_manager_postgres import DatabaseManagerPostgres
from user import User
from utils import ParsedData


class Response:
    def __init__(self, input_data, server):
        self.input_data = input_data
        self.server = server
        self.parsed_input = None
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
        self.parsed_input = ParsedData(self.input_data)

        match self.parsed_input.command:
            case 'uptime':
                return f'Server uptime: {round(self.server.uptime, 2)} s'
            case 'help':
                return f'Available commands:\n' \
                       f'"help" - get the commands list\n' \
                       f'"login <username> <password>" - log in to the server\n' \
                       f'"signup <username> <password>" - create new account\n' \
                       f'"users" - list of users on the server; log in first\n' \
                       f'"whisper <username> <message>" - send a message to the selected user; log in first\n' \
                       f'"conversation" - shows usernames you have a conversation with; log in first\n' \
                       f'"conversation <username>" - shows messages between you and selected user; log in first\n' \
                       f'"uptime" - get server lifetime\n' \
                       f'"info" - get server version\n' \
                       f'"stop" - stops both the client and the server\n'
            case 'info':
                return f'Server version: {self.server.version}'
            case 'stop':
                return None
            case 'signup':
                return self.signup_response()
            case 'login':
                return self.login_response()
            case 'users':
                return self.credentials_check(self.list_response)
            case 'whisper':
                return self.credentials_check(self.whisper_response)
            case 'unread':
                return self.credentials_check(self.unread_response)
            case 'conversation':
                return self.credentials_check(self.conversation_response)
        return 'Unknown command'

    def login_response(self):
        name, pw = self.parsed_input.name, self.parsed_input.password
        if name and pw:
            user = User(name, pw)
            if user.credentials_ok:
                r = f'Logged in as {name}'
                if user.permission == 'ADMIN':
                    r += ' (admin)'
                return r
            return 'Incorrect credentials.'
        return 'Make sure to provide username and password.'

    def signup_response(self):
        name, pw = self.parsed_input.name, self.parsed_input.password
        if name and pw:
            user = User(name, pw)
            if user.in_database:
                return 'This username is already taken.'
            r = DatabaseManagerPostgres.instance.add_user(user)
            if r[0]:
                return f'User created: {user.name}'
            return f'Error creating user: {r[1]}'
        return 'Make sure to provide username and password.'

    def credentials_check(self, inner):
        name, pw = self.parsed_input.name, self.parsed_input.password
        if name and pw:
            user = User(name, pw)
            if user.credentials_ok:
                return inner(user)
            return 'Incorrect credentials.'
        return 'Log in first.'

    def list_response(self, user):
        return ', '.join(User.get_all_usernames())

    def unread_response(self, user):
        unread = user.unread_messages
        if len(unread) > 0:
            r = 'Unread messages:'
            for msg in unread:
                r += f'\nFrom: "{msg.sender_name}", Message: "{msg.content}", Time sent: "{msg.time_sent}"'
                msg.read_by_recipient = True
                DatabaseManagerPostgres.instance.update_message(msg)
            return r
        return 'There are no new messages.'

    def whisper_response(self, user):
        recipient_name, msg = self.parsed_input.arg1, self.parsed_input.arg2
        if recipient_name and msg:
            if recipient_name in User.get_all_usernames():
                if recipient_name != user.name:
                    if User.get_user_by_name(recipient_name).get_unread_count() < 5:
                        if len(msg) <= 255:
                            from message import Message
                            r = DatabaseManagerPostgres.instance.add_message(Message(user.name, recipient_name, msg))
                            if r[0]:
                                return f'Message "{msg}" sent to "{recipient_name}"'
                            return f'Error creating message: {r[1]}'
                        return 'Too long message. Maximum character count is 255.'
                    return f'Mailbox of user "{recipient_name}" is full. You cannot send another message.'
                return 'You cannot whisper yourself.'
            return f'User "{recipient_name}" does not exist on the server.'
        return 'Username or message not provided.'

    def conversation_response(self, user):
        if self.parsed_input.arg1 is None and self.parsed_input.arg2 is None:
            conversations = sorted(user.get_conversations())
            if len(conversations) > 0:
                return f'You have conversations with these users: {", ".join(conversations)}'
            return 'You have no conversations with other users.'

        elif self.parsed_input.arg1 and self.parsed_input.arg2 is None:
            other_name = self.parsed_input.arg1
            messages = user.get_messages_with_other(other_name)
            if len(messages) > 0:
                r = f'Messages with "{other_name}" (oldest to newest):'
                for msg in sorted(messages, key=lambda x: x.time_sent):
                    r += f'\n{msg.sender_name}: {msg.content}'
                return r
            return f'You have no messages with {other_name}.'

        elif self.parsed_input.arg1 and self.parsed_input.arg2:
            # admin only
            if user.permission == 'ADMIN':
                username1 = self.parsed_input.arg1
                username2 = self.parsed_input.arg2
                messages = User.get_messages(username1, username2)
                if len(messages) > 0:
                    r = f'Messages between "{username1}" and "{username2}" (oldest to newest):'
                    for msg in sorted(messages, key=lambda x: x.time_sent):
                        r += f'\n{msg.sender_name}: {msg.content}'
                    return r
                return f'There are no messages between "{username1}" and "{username2}".'

            return 'Only ADMIN can access other users conversations.'
