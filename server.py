import datetime
import re
import socket
import string
import time
import json

from database_manager import DatabaseManager
from response import Response


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
