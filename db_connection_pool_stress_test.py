import threading
import time

import database_manager
from db_config import db_params

if __name__ == "__main__":
    # RUN THIS SCRIPT TO STRESS TEST DATABASE CONNECTION POOL WITH MULTIPLE CONCURRENT QUERIES

    db_manager = database_manager.DatabaseManager(*db_params, time_limit_of_db_conn_pool_update=300)

    def perform_database_query():
        # THOUSANDS OF USERNAMES SO IT SHOULD TAKE A WHILE
        response = db_manager.get_usernames()
        return response


    start_time = time.perf_counter()

    threads = []
    while db_manager.is_active():
        thread = threading.Thread(target=perform_database_query)
        thread.start()
        threads.append(thread)

    for thread in threads:
        thread.join()

    end_time = time.perf_counter()
    print(f'Total execution time: {round((end_time - start_time) * 1000, 2)} ms')

    db_manager.stop_db_connections()
