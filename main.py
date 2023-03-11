from db_config import db_params
from server import Server

HOST = "127.0.0.1"
PORT = 65432

server = Server(HOST, PORT, version='0.3.0', db_params=db_params, concurrent_settings=['PARALLEL_USERS'])

server.start()
