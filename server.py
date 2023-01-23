import datetime
import re
import socket
import string
import time
import json


class Permission:
    USER = 'USER',
    ADMIN = 'ADMIN'


class User:
    def __init__(self, name, password, permission=Permission.USER):
        self.name = name
        self.password = password
        self.permission = permission

    def __eq__(self, other):
        return self.name == other.name

    def get_conversations(self):
        ...

    def get_unread_message(self):
        ...

    def get_usernames(self):
        ...

    def send_message(self):
        ...


class Message:
    def __init__(self, sender, recipient, content, read_by_recipient=False, time_sent=datetime.datetime.now()):
        self.sender = sender
        self.recipient = recipient
        self.content = content
        self.read_by_recipient = read_by_recipient
        self.time_sent = time_sent


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
                       f'"uptime" - get server lifetime\n' \
                       f'"info" - get server version\n' \
                       f'"stop" - stops both the client and the server\n'
            case 'info':
                return f'Server version: {self.server.version}'
            case 'stop':
                return None
            case 'signup':
                return self.user_signup()
        return 'Unknown command'

    def user_signup(self):
        r = re.compile(r'(signup)\s(\S+)\s(\S+)')
        match = r.match(self.input_data)
        if match and len(match.groups()) == 3:
            print(match.groups())
            name = match[2]
            pw = match[3]

            user = User(name, pw)
            if user in DatabaseManager.get_users():
                return 'This username is already taken.'

            DatabaseManager.add_user(user)
            return f'User created: {name}'


class DatabaseManager:
    db = {}

    @classmethod
    def read_db(cls):
        try:
            with open('db.json', 'r') as db:
                cls.db = json.loads(db.read())
                cls.deserialize()
                return cls.db
        except FileNotFoundError:
            cls.db = {
                'users': [],
                'messages': [],
            }
            cls.save_db()

    @classmethod
    def save_db(cls):
        with open('db.json', 'w') as db:
            db.write(json.dumps(cls.serialize()))

    @classmethod
    def deserialize(cls):
        cls.db['users'] = [User(user['name'], user['password'], user['permission']) for user in cls.db['users']]
        cls.db['messages'] = [
            Message(msg['sender'], msg['recipient'], msg['content'], msg['read_by_recipient'], msg['time_sent']) for msg
            in cls.db['messages']]

    @classmethod
    def serialize(cls):
        cls.db['users'] = [user.__dict__ for user in cls.db['users']]
        cls.db['messages'] = [message.__dict__ for message in cls.db['messages']]
        return cls.db

    @classmethod
    def get_users(cls):
        return [user for user in cls.db['users']]

    @classmethod
    def get_messages(cls):
        return [message for message in cls.db['messages']]

    @classmethod
    def add_user(cls, user):
        cls.db['users'].append(user)

    @classmethod
    def add_message(cls, msg):
        cls.db['messages'].append(msg)


class Server:
    def __init__(self, host, port, version='0.1.0'):
        self.host = host
        self.port = port
        self.version = version
        self.time_start = 0
        self.up = True
        DatabaseManager.read_db()

    @property
    def uptime(self):
        return time.time() - self.time_start

    def start(self):
        self.time_start = time.time()

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((self.host, self.port))
            s.listen()
            conn, addr = s.accept()
            with conn:
                print(f"Connected by {addr}")
                while self.up:
                    self.update(conn)

    def update(self, conn):
        client_data = conn.recv(1024)
        server_response = Response(client_data, self)

        if not server_response.data:
            DatabaseManager.save_db()
            self.up = False
        else:
            server_response.as_json
            print(f'Sending response in json: {server_response.data}')
            conn.sendall(server_response.as_bytes.data)
