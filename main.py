from server import Server

HOST = "127.0.0.1"
PORT = 65432

server = Server(HOST, PORT, version='0.2.0')
server.start()
