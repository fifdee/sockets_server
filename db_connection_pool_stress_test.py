import threading
import time

import database_manager_postgres

if __name__ == "__main__":
    # RUN THIS SCRIPT TO STRESS TEST DATABASE CONNECTION POOL WITH MULTIPLE CONCURRENT QUERIES
    db_manager = database_manager_postgres.DatabaseManagerPostgres("172.24.163.127", "server_db", "dev", "dev", 300)


    def perform_database_query():
        # THOUSANDS OF USERNAMES SO IT SHOULD TAKE A WHILE
        r = db_manager.get_usernames()
        return r


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
