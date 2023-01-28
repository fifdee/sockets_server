import datetime
import json
import os

from message import Message
from user import User


class DatabaseManager:
    db = {}
    test = False

    @classmethod
    def read_db(cls):
        try:
            db_path = 'db.json'
            if cls.test:
                db_path = 'test_' + db_path

            with open(db_path, 'r') as db:
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
        db_path = 'db.json'
        if cls.test:
            db_path = 'test_' + db_path

        with open(db_path, 'w') as db:
            db.write(json.dumps(cls.serialize()))

    @classmethod
    def remove_test_db(cls):
        try:
            os.remove('test_db.json')
        except FileNotFoundError:
            ...

    @classmethod
    def deserialize(cls):
        cls.db['users'] = [User(user['name'], user['password'], user['permission']) for user in cls.db['users']]
        cls.db['messages'] = [
            Message(msg['sender_name'], msg['recipient_name'], msg['content'], msg['read_by_recipient'],
                    datetime.datetime.strptime(msg['time_sent'], "%m/%d/%Y, %H:%M:%S.%f")) for msg in cls.db['messages']]

    @classmethod
    def serialize(cls):
        cls.db['users'] = [user.__dict__ for user in cls.db['users']]
        cls.db['messages'] = [{
            'sender_name': message.sender_name,
            'recipient_name': message.recipient_name,
            'content': message.content,
            'read_by_recipient': message.read_by_recipient,
            'time_sent': message.time_sent.strftime("%m/%d/%Y, %H:%M:%S.%f")
        } for message in cls.db['messages']]
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
