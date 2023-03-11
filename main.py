from server import Server

HOST = "127.0.0.1"
PORT = 65432

db_params = ("172.24.163.127", "server_db", "dev", "dev")
db_params_sqlite = (None, 'server_db.db', None, None)

server = Server(HOST, PORT, version='0.3.0', db_params=db_params_sqlite, concurrent_settings=['PARALLEL_USERS'])

server.start()
