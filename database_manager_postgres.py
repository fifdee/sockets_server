import time

from psycopg2 import Error
from sqlite3 import Error as Error_sqlite

from db_connection_pool import ConnectionPool
from message import Message
from user import User


class DatabaseManager:
    instance = None

    def __init__(self, host, database, user, password, time_limit_of_db_conn_pool_update=None):
        if not time_limit_of_db_conn_pool_update:
            self.connection_pool = ConnectionPool(host, database, user, password)
        else:
            self.connection_pool = ConnectionPool(host, database, user, password, time_limit_of_db_conn_pool_update)
        self.queries = []
        DatabaseManager.instance = self

    def stop_db_connections(self):
        self.connection_pool.disconnect_all()

    def is_active(self):
        return self.connection_pool.is_performing_update_method()

    def _deserialize(self, fetched_obj, fetched_obj_class):
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

    def _serialize(self, python_obj):
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

    def _send_query(self, query):
        try:
            conn = self.connection_pool.get_connection()
            if conn:
                cur = conn.cursor()
                cur.execute(query)

                if query.split()[0] == "SELECT":
                    response = cur.fetchall()
                    self.queries.append(True)
                    self.connection_pool.release_connection(conn)
                    return response
                else:
                    conn.commit()
                    self.queries.append(True)
                    self.connection_pool.release_connection(conn)
                    return True, None
            else:
                # Could not obtain connection object, repeating query
                time.sleep(2)
                return self._send_query(query)

        except Error or Error_sqlite as e:
            # Error, repeating query
            print(e)
            time.sleep(2)
            return self._send_query(query)

    def get_user(self, username):
        query = f"SELECT name, password, permission FROM users WHERE name = '{username}';"

        response = self._send_query(query)
        if len(response) > 0:
            return self._deserialize(response[0], User)
        else:
            return None

    def get_usernames(self):
        query = "SELECT name FROM users;"
        response = self._send_query(query)
        try:
            return [fetched_tuple[0] for fetched_tuple in response]
        except Exception as e:
            return ['Invalid response for "get_usernames()"', e]

    def get_messages(self, username1, username2=None):
        if username2:
            query = f"SELECT sender_name, recipient_name, content, read_by_recipient, time_sent FROM messages " \
                    f"WHERE (sender_name = '{username1}' AND recipient_name = '{username2}') OR " \
                    f"(sender_name = '{username2}' AND recipient_name = '{username1}');"
        else:
            query = f"SELECT sender_name, recipient_name, content, read_by_recipient, time_sent FROM messages " \
                    f"WHERE (sender_name = '{username1}' OR recipient_name = '{username1}');"

        response = self._send_query(query)
        try:
            deserialized = [self._deserialize(x, Message) for x in response]
            return deserialized
        except Exception as e:
            return ['Invalid response for "get_messages()"', e]

    def get_unread_messages(self, username):
        query = f"SELECT sender_name, recipient_name, content, read_by_recipient, time_sent FROM messages " \
                f"WHERE (recipient_name = '{username}' AND read_by_recipient = false);"

        try:
            deserialized = [self._deserialize(x, Message) for x in self._send_query(query)]
            return deserialized
        except Exception as e:
            return ['Invalid response for "get_unread_messages()"', e]

    def add_user(self, user):
        serialized = self._serialize(user)
        query = f"INSERT INTO users (name, password, permission) values ('{serialized[0]}', '{serialized[1]}', " \
                f"'{serialized[2]}');"
        return self._send_query(query)

    def add_message(self, msg):
        serialized = self._serialize(msg)
        query = f"INSERT INTO messages (sender_name, recipient_name, content, read_by_recipient, time_sent) values " \
                f"('{serialized[0]}', '{serialized[1]}', '{serialized[2]}', {serialized[3]}, '{serialized[4]}');"
        return self._send_query(query)

    def messages_as_read(self, recipient_name):
        query = f"UPDATE messages SET read_by_recipient = true WHERE " \
                f"(recipient_name = '{recipient_name}');"
        return self._send_query(query)

    def clear_users_table(self):
        # query = 'TRUNCATE TABLE users;'
        query = 'DELETE FROM users;'
        self._send_query(query)

    def clear_messages_table(self):
        # query = 'TRUNCATE TABLE messages;'
        query = 'DELETE FROM messages;'
        self._send_query(query)
