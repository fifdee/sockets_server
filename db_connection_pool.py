import concurrent.futures
import random
import threading
import time
from datetime import datetime

import psycopg2
from psycopg2 import Error


class ConnectionInfo:
    def __init__(self, connection, i):
        self.connection = connection
        self.in_use = False
        self.id = i


class ConnectionPool:
    def __init__(self, host, database, user, password):
        self.host = host
        self.database = database
        self.user = user
        self.password = password

        self.connections_at_start = 5
        self.conn_infos = [ConnectionInfo(self._connect(), i) for i in range(self.connections_at_start)]
        self.returned_connections_count = 0

        self.active = True
        self.prev_t = time.perf_counter()
        self.time_passed = 0

        self.time_to_update = 30

        self.semaphore = threading.Semaphore()

        t_updt = threading.Thread(target=self._update)
        t_updt.start()

    def is_active(self):
        return self.active

    def _update(self):
        while self.active:
            delta = time.perf_counter() - self.prev_t
            self.time_passed += delta

            conns_to_delete = [conn for conn in self.conn_infos if
                               (not conn.in_use) and (conn.id >= self.connections_at_start)]
            self.semaphore.acquire()
            for c in conns_to_delete:
                c.connection.close()
                self.conn_infos.remove(c)
            self.semaphore.release()

            print(f'Current conns count: {len(self.conn_infos)}, '
                  f'Returned conns: {self.returned_connections_count}, '
                  f'time passed: {round(self.time_passed, 2)} s')

            self.prev_t = time.perf_counter()
            time.sleep(2)

            if self.time_to_update != 'infinite':
                if self.time_passed > self.time_to_update:
                    self.active = False

    def _connect(self):
        try:
            conn = psycopg2.connect(
                host=self.host,
                database=self.database,
                user=self.user,
                password=self.password,
            )
            return conn
        except Error as error:
            print("Error while connecting to Database.", error)

    def get_connection(self):
        not_used = [conn for conn in self.conn_infos if not conn.in_use]
        if len(not_used) == 0:
            if len(self.conn_infos) > 50:
                print('Too many active DB connections (>50)')
                return None
            else:
                new = ConnectionInfo(self._connect(), len(self.conn_infos) + 1)
                new.in_use = True
                self.semaphore.acquire()
                self.conn_infos.append(new)
                self.returned_connections_count += 1
                self.semaphore.release()
                return new.connection
        else:
            self.semaphore.acquire()
            not_used[0].in_use = True
            self.returned_connections_count += 1
            self.semaphore.release()
            return not_used[0].connection

    def release_connection(self, conn):
        conn_info = [c_inf for c_inf in self.conn_infos if c_inf.connection == conn][0]
        self.semaphore.acquire()
        conn_info.in_use = False
        self.semaphore.release()

    def disconnect_all(self):
        self.semaphore.acquire()
        for c in self.conn_infos:
            c.connection.close()
        self.active = False
        self.semaphore.release()
