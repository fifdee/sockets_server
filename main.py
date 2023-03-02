from server import Server

HOST = "127.0.0.1"
PORT = 65432

db_params = ("172.24.163.127", "server_db", "dev", "dev")

server = Server(HOST, PORT, version='0.3.0', db_params=db_params, concurrent_settings=['PARALLEL_USERS'])

server.start()
