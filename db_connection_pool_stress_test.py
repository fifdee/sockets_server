import threading
import time

import database_manager_postgres

if __name__ == "__main__":
    db_manager = database_manager_postgres.DatabaseManagerPostgres("172.24.163.127", "server_db", "dev", "dev")


    def f():
        r = db_manager.get_usernames()
        return r


    t1 = time.perf_counter()

    threads = []
    while db_manager.is_active():
        t = threading.Thread(target=f)
        t.start()
        threads.append(t)

    for t in threads:
        t.join()

    # while db_manager.is_active():
    #     f()

    t2 = time.perf_counter()
    print(f'Total execution time: {round((t2 - t1) * 1000, 2)} ms')

    db_manager.stop()
