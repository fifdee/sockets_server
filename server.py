import socket
import time
import json


class Server:
    def __init__(self, host, port, version='0.1.0'):
        self.host = host
        self.port = port
        self.uptime = 0
        self.version = version
        self.time_start = 0

    def start(self):
        self.time_start = time.time()

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((self.host, self.port))
            s.listen()
            conn, addr = s.accept()
            with conn:
                print(f"Connected by {addr}")
                while True:
                    self.update_uptime()

                    client_data = conn.recv(1024)

                    server_response = self.response_data(client_data)
                    if not server_response:
                        break
                    else:
                        server_response = json.dumps(server_response)
                        print(f'Sending response in json: {server_response}')
                        conn.sendall(bytes(server_response, 'utf-8'))

    def update_uptime(self):
        self.uptime = time.time() - self.time_start

    def response_data(self, command):
        match command:
            case b'uptime':
                return f'Server uptime: {round(self.uptime, 2)} s'
            case b'help':
                return f'Available commands:\n' \
                       f'help - get the commands list\n' \
                       f'uptime - get server lifetime\n' \
                       f'info - get server version\n' \
                       f'stop - stops both the client and the server\n'
            case b'info':
                return f'Server version: {self.version}'
            case b'stop':
                return None
        return 'Unknown command'
