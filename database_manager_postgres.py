import time

from psycopg2 import Error

from db_connection_pool import ConnectionPool
from message import Message
from user import User


class DatabaseManagerPostgres:
    instance = None

    def __init__(self, host, database, user, password):
        self.connection_pool = ConnectionPool(host, database, user, password)
        DatabaseManagerPostgres.instance = self

    def deserialize(self, fetched_obj, fetched_obj_class):
        if fetched_obj_class == User:
            return User(fetched_obj[0], fetched_obj[1], fetched_obj[2])
        elif fetched_obj_class == Message:
            return Message(
                sender_name=fetched_obj[0],
                recipient_name=fetched_obj[1],
                content=fetched_obj[2],
                read_by_recipient=fetched_obj[3],
                time_sent=fetched_obj[4]
            )
        else:
            raise Exception(f'Could not deserialize {type(fetched_obj_class)} object.')

    def serialize(self, python_obj):
        if isinstance(python_obj, User):
            return (
                python_obj.name,
                python_obj.password,
                python_obj.permission
            )
        elif isinstance(python_obj, Message):
            return (
                python_obj.sender_name,
                python_obj.recipient_name,
                python_obj.content,
                python_obj.read_by_recipient,
                python_obj.time_sent
            )
        else:
            raise Exception(f'Could not serialize {type(python_obj)} object.')

    def get_user(self, username):
        query = f"SELECT name, password, permission FROM users WHERE name = '{username}';"

        r = self.connection_pool.send_query(query)
        if len(r) > 0:
            return self.deserialize(r[0], User)
        else:
            return None

    def get_usernames(self):
        query = "SELECT name FROM users;"
        return [fetched_tuple[0] for fetched_tuple in self.connection_pool.send_query(query)]

    def get_messages(self, username1, username2=None):
        if username2:
            query = f"SELECT sender_name, recipient_name, content, read_by_recipient, time_sent FROM messages " \
                    f"WHERE (sender_name = '{username1}' AND recipient_name = '{username2}') OR " \
                    f"(sender_name = '{username2}' AND recipient_name = '{username1}');"
        else:
            query = f"SELECT sender_name, recipient_name, content, read_by_recipient, time_sent FROM messages " \
                    f"WHERE (sender_name = '{username1}' OR recipient_name = '{username1}');"

        deserialized = [self.deserialize(x, Message) for x in self.connection_pool.send_query(query)]
        return deserialized

    def get_unread_messages(self, username):
        query = f"SELECT sender_name, recipient_name, content, read_by_recipient, time_sent FROM messages " \
                f"WHERE (recipient_name = '{username}' AND read_by_recipient = false);"

        deserialized = [self.deserialize(x, Message) for x in self.connection_pool.send_query(query)]
        return deserialized

    def add_user(self, user):
        serialized = self.serialize(user)
        query = f"INSERT INTO users (name, password, permission) values ('{serialized[0]}', '{serialized[1]}', " \
                f"'{serialized[2]}');"
        return self.connection_pool.send_query(query)

    def add_message(self, msg):
        serialized = self.serialize(msg)
        query = f"INSERT INTO messages (sender_name, recipient_name, content, read_by_recipient, time_sent) values " \
                f"('{serialized[0]}', '{serialized[1]}', '{serialized[2]}', {serialized[3]}, TIMESTAMP '{serialized[4]}');"
        return self.connection_pool.send_query(query)

    def messages_as_read(self, recipient_name):
        query = f"UPDATE messages SET read_by_recipient = true WHERE " \
                f"(recipient_name = '{recipient_name}');"
        return self.connection_pool.send_query(query)

    def clear_users_table(self):
        query = 'TRUNCATE TABLE users;'
        self.connection_pool.send_query(query)

    def clear_messages_table(self):
        query = 'TRUNCATE TABLE messages;'
        self.connection_pool.send_query(query)
