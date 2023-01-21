import socket
import time
import json


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
        match self.input_data:
            case 'uptime':
                return f'Server uptime: {round(self.server.uptime, 2)} s'
            case 'help':
                return f'Available commands:\n' \
                       f'help - get the commands list\n' \
                       f'uptime - get server lifetime\n' \
                       f'info - get server version\n' \
                       f'stop - stops both the client and the server\n'
            case 'info':
                return f'Server version: {self.server.version}'
            case 'stop':
                return None
        return 'Unknown command'


class Server:
    def __init__(self, host, port, version='0.1.0'):
        self.host = host
        self.port = port
        self.version = version
        self.time_start = 0
        self.up = True

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
            self.up = False
        else:
            server_response.as_json
            print(f'Sending response in json: {server_response.data}')
            conn.sendall(server_response.as_bytes.data)
