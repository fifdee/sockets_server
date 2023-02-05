import sys

import psycopg2 as psycopg2
from psycopg2 import Error

from message import Message
from user import User


class DatabaseManagerPostgres:
    instance = None

    def __init__(self, host, database, user, password):
        self.host = host
        self.database = database
        self.user = user
        self.password = password

        DatabaseManagerPostgres.instance = self

    def connect(self):
        try:
            conn = psycopg2.connect(
                host=self.host,
                database=self.database,
                user=self.user,
                password=self.password
            )
            cur = conn.cursor()
            return conn, cur
        except Error as error:
            print("Error while connecting to PostgreSQL, shutting down server.", error)
            sys.exit()

    def disconnect(self, conn, cur):
        cur.close()
        conn.close()

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

        try:
            conn, cur = self.connect()
            cur.execute(query)
            r = cur.fetchall()
            self.disconnect(conn, cur)
            if len(r) > 0:
                return self.deserialize(r[0], User)

        except Error as e:
            print(e)
        else:
            return None

    def get_usernames(self):
        query = "SELECT name FROM users;"
        conn, cur = self.connect()
        cur.execute(query)
        r = cur.fetchall()
        self.disconnect(conn, cur)

        return [fetched_tuple[0] for fetched_tuple in r]

    def get_messages(self, username1, username2=None):
        if username2:
            query = f"SELECT sender_name, recipient_name, content, read_by_recipient, time_sent FROM messages " \
                    f"WHERE (sender_name = '{username1}' AND recipient_name = '{username2}') OR " \
                    f"(sender_name = '{username2}' AND recipient_name = '{username1}');"
        else:
            query = f"SELECT sender_name, recipient_name, content, read_by_recipient, time_sent FROM messages " \
                    f"WHERE (sender_name = '{username1}' OR recipient_name = '{username1}');"
        conn, cur = self.connect()
        cur.execute(query)
        r = cur.fetchall()
        self.disconnect(conn, cur)
        deserialized = [self.deserialize(x, Message) for x in r]
        return deserialized

    def get_unread_messages(self, username):
        query = f"SELECT sender_name, recipient_name, content, read_by_recipient, time_sent FROM messages " \
                f"WHERE (recipient_name = '{username}' AND read_by_recipient = false);"
        conn, cur = self.connect()
        cur.execute(query)
        r = cur.fetchall()
        self.disconnect(conn, cur)
        deserialized = [self.deserialize(x, Message) for x in r]
        return deserialized

    def add_user(self, user):
        serialized = self.serialize(user)
        query = f"INSERT INTO users (name, password, permission) values ('{serialized[0]}', '{serialized[1]}', " \
                f"'{serialized[2]}');"
        return self.send_commit_query(query)

    def add_message(self, msg):
        serialized = self.serialize(msg)
        query = f"INSERT INTO messages (sender_name, recipient_name, content, read_by_recipient, time_sent) values " \
                f"('{serialized[0]}', '{serialized[1]}', '{serialized[2]}', {serialized[3]}, TIMESTAMP '{serialized[4]}');"
        return self.send_commit_query(query)

    def update_message(self, msg):
        serialized = self.serialize(msg)
        query = f"UPDATE messages SET read_by_recipient = true WHERE " \
                f"(sender_name = '{serialized[0]}' AND recipient_name = '{serialized[1]}' AND time_sent = TIMESTAMP '{serialized[4]}');"
        return self.send_commit_query(query)

    def send_commit_query(self, query):
        try:
            conn, cur = self.connect()
            cur.execute(query)
            conn.commit()
            self.disconnect(conn, cur)
        except Error as e:
            print(e)
            return False, e
        else:
            return True, None

    def clear_users_table(self):
        query = 'TRUNCATE TABLE users;'
        self.send_commit_query(query)

    def clear_messages_table(self):
        query = 'TRUNCATE TABLE messages;'
        self.send_commit_query(query)
