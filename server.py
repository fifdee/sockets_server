import json
import socket
import sys
import threading
import time

from database_manager_postgres import DatabaseManager
from response import Response


class Query:
    def __init__(self, data, connection, address):
        self.data = data
        self.connection = connection
        self.address = address

    def __repr__(self):
        return f'{self.data} /// address: {self.address}'


class Server:
    def __init__(self, host, port, version='0.1.0', db_params=None,
                 concurrent_settings=('PARALLEL_QUERIES', 'PARALLEL_USERS')):
        self.host = host
        self.port = port
        self.version = version
        self.time_start = 0
        self.up = True
        self.db_mngr = DatabaseManager(*db_params)
        self.responses_no = 0
        self.concurrent_settings = concurrent_settings

        self.queries = []
        self.responses = []

    @property
    def uptime(self):
        return time.time() - self.time_start

    def start(self):
        self.time_start = time.time()

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((self.host, self.port))
            s.listen()

            while self.up:
                conn, addr = s.accept()
                print(f'New connection: {addr}')

                def updt(conn_, addr_):
                    with conn_:
                        print(f"Connected by {addr_}, uptime: {self.uptime}")
                        while self.update(conn_, addr_):
                            ...

                if 'PARALLEL_USERS' in self.concurrent_settings:
                    t = threading.Thread(target=updt, args=[conn, addr])
                    t.start()
                else:
                    updt(conn, addr)

    def update(self, conn, addr):
        try:
            client_data = conn.recv(1024)
        except OSError as e:
            print(e)
            return False
        else:
            print(f'client_data: {client_data}')
            if not client_data:
                print(f'No client data, closing connection: {conn}')
                conn.close()
                return False

            self.queries.append(Query(client_data, conn, addr))
            print(self.queries)

            def pop_query_create_response():
                if len(self.queries) > 0:
                    q = self.queries.pop()
                    Response(q.data, self, q.connection, q.address)

            for _ in self.queries:
                if 'PARALLEL_QUERIES' in self.concurrent_settings:
                    t = threading.Thread(target=pop_query_create_response)
                    t.start()
                else:
                    pop_query_create_response()

            while len(Response.responses) > 0:
                self.responses.append(Response.responses.pop())

            response_to_send = b'"blank response"'
            for i in range(len(self.responses)):
                if self.responses[i].address == addr:
                    self.responses_no += 1

                    if len(self.responses) > 0:
                        popped = self.responses.pop(i)
                        print(f'Response size: {sys.getsizeof(popped.data)}')
                        response_to_send = bytes(json.dumps(popped.data), 'utf-8')
                        print(f'Response sending: {response_to_send[:100]}[...], response no: {self.responses_no}')
                        break

            conn.sendall(response_to_send)

            return True
