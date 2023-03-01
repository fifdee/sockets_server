import concurrent.futures
import random
import threading
import time
from datetime import datetime

import psycopg2
from psycopg2 import Error


class ConnectionInfo:
    def __init__(self, connection, cursor, i):
        self.connection = connection
        self.cursor = cursor
        self.in_use = False
        self.id = i


class ConnectionPool:
    def __init__(self, host, database, user, password):
        self.host = host
        self.database = database
        self.user = user
        self.password = password

        self.connections_at_start = 5
        self.conn_infos = [ConnectionInfo(*self.connect(), i) for i in range(self.connections_at_start)]
        self.max_no_conns = 0

        self.i = 0
        self.queries = []

        self.active = True
        self.prev_t = time.perf_counter()
        self.time_passed = 0

    def update(self):
        while self.active:
            delta = time.perf_counter() - self.prev_t
            self.time_passed += delta

            conns_to_delete = [conn for conn in self.conn_infos if
                               (not conn.in_use) and (conn.id >= self.connections_at_start)]
            for c in conns_to_delete:
                self.conn_infos.remove(c)

            print(f'Current conns count: {len(self.conn_infos)}, '
                  f'queries count: {len(self.queries)}, '
                  f'time passed: {round(self.time_passed, 2)} s')

            self.prev_t = time.perf_counter()
            time.sleep(1)

            if self.time_passed > 15:
                self.active = False

    def connect(self):
        try:
            conn = psycopg2.connect(
                host=self.host,
                database=self.database,
                user=self.user,
                password=self.password,
            )
            cursor = conn.cursor()
            return conn, cursor
        except Error as error:
            print("Error while connecting to Database.", error)

    def get_conn(self):
        if len(self.conn_infos) > self.max_no_conns:
            self.max_no_conns = len(self.conn_infos)

        not_used = [conn for conn in self.conn_infos if not conn.in_use]
        if len(not_used) == 0:
            if len(self.conn_infos) > 50:
                print('Too many active DB connections (>50)')
                return None
            else:
                new = ConnectionInfo(*self.connect(), len(self.conn_infos) + 1)
                new.in_use = True
                self.conn_infos.append(new)
                return new
        else:
            not_used[0].in_use = True
            return not_used[0]

    def disconnect_all(self):
        for c in self.conn_infos:
            c.cursor.close()
            c.connection.close()

    def send_query(self, query):
        conn = None
        try:
            conn = self.get_conn()
            if conn:
                con = conn.connection
                cur = conn.cursor
                cur.execute(query)

                conn.in_use = False

                if query.split()[0] == "SELECT":
                    r = cur.fetchall()
                    return r
                else:
                    con.commit()
                    return True, None
        except Error as e:
            if conn:
                if len([c for c in self.conn_infos if not c.in_use]) == 0:
                    self.conn_infos.remove(conn)
                    new = ConnectionInfo(*self.connect(), len(self.conn_infos) + 1)
                    self.conn_infos.append(new)
            print(f'send_query() error: {e}')
            return False, e


if __name__ == '__main__':
    # STRESS TEST WITH MULTIPLE PARALLEL CONNECTIONS TO DATABASE
    db_conn_pool = ConnectionPool("172.24.170.212", "server_db", "dev", "dev")

    queries = [
        f"INSERT INTO messages (sender_name, recipient_name, content, read_by_recipient, time_sent) values "
        f"('second_user', 'fifdee', 'hello message', FALSE, TIMESTAMP '{datetime.now()}');",

        f"SELECT sender_name, recipient_name, content, read_by_recipient, time_sent FROM messages "
        f"WHERE (recipient_name = 'fifdee' AND read_by_recipient = false);",

        "SELECT name FROM users;",
    ]

    t_updt = threading.Thread(target=db_conn_pool.update)
    t_updt.start()

    def f():
        r = db_conn_pool.send_query(random.choice(queries))
        db_conn_pool.queries.append(True)
        return r


    t1 = time.perf_counter()

    threads = []
    while db_conn_pool.active:
        t = threading.Thread(target=f)
        t.start()
        threads.append(t)

    for t in threads:
        t.join()

    t2 = time.perf_counter()
    print(f'Total execution time: {round((t2 - t1) * 1000, 2)} ms')

    db_conn_pool.disconnect_all()
