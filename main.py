from server import Server

HOST = "127.0.0.1"
PORT = 65432

db_params = ("172.17.101.178", "server_db", "dev", "dev")

server = Server(HOST, PORT, version='0.3.0', db_params=db_params)
server.start()
