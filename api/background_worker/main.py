import time

from loguru import logger
from psycopg2 import OperationalError, InterfaceError

from service import get_connection, start_process, update_global_connections, write_status_connect, restart_process
from db_service import create_connection

work_proc = {}
restart_list = []
STATUS_LIST = {}

print("Connect to DB ...")
conn_db, cursor_db = create_connection()
print("DONE")

print("Get list of connection ...")
connection_list = get_connection(cursor=cursor_db)
print("DONE")

print('Start processes ...')
for con in connection_list:
    proc, status, stop = start_process(con)
    if proc:
        work_proc[con.name] = {
            'process': proc,
            'status': status,
            'stop_point': stop
        }
        STATUS_LIST[con.name] = status.value
    else:
        restart_list.append(con)
print("DONE")

while True:
    try:
        new_connections = get_connection(cursor_db)
        if connection_list != new_connections:
            update_global_connections(connection_list, new_connections, work_proc, restart_list, connect=conn_db,
                cursor=cursor_db,)
        for key in work_proc:
            write_status_connect(
                connect=conn_db,
                cursor=cursor_db,
                name_connection=key,
                status_connect=work_proc[key]['status'].value,
                status_process=work_proc[key]['process'].is_alive()
            )
            print(f'status {key}: ', work_proc[key]['status'].value)
        restart_process(restart_list=restart_list, work_process=work_proc)
        time.sleep(1)
    except OperationalError:
        logger.error("BAD DB CONNECT")
    except InterfaceError:
        logger.error("BAD DB CONNECT")
        time.sleep(5)
        connection_db, cursor_db = create_connection()
