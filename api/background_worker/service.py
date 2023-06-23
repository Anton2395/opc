import multiprocessing as mp
from ctypes import c_bool
import cprint

from processorMod import ConnectModProcess
from processorSnap import ConnectSnapProcess
from classType import ConnectionItem, AreaItem, ValueItem


def start_process(param_connection: ConnectionItem) -> list:
    try:
        status = mp.Value(c_bool, False)
        stop = mp.Value(c_bool, False)
        if param_connection.driver == 'ModbusTCP':
            process = ConnectModProcess(
                name_connect=param_connection.name,
                ip=param_connection.ip,
                port=param_connection.port,
                status=status,
                stop_point=stop,
                areas=param_connection.area
            )
            process.start()
        elif param_connection.driver == 'Snap7':
            process = ConnectSnapProcess(
                name_connect=param_connection.name,
                ip=param_connection.ip,
                port=param_connection.port,
                rack=param_connection.rack,
                slot=param_connection.slot,
                status=status,
                stop_point=stop,
                areas=param_connection.area
            )
            process.start()
        else:
            process = None
            status = None
            stop = None
        cprint.cprint.info("Start " + param_connection.name)
    except:
        process = None
        status = None
        stop = None
    return [process, status, stop]


def stop_process(process_object: dict):
    """
    TODO: change status when stop process
    """
    while process_object['process'].is_alive():
        process_object['process'].terminate()
        process_object['stop_point'].value = True
    cprint.cprint.info("Stop " + process_object['process'].name_connect)
    return True


def update_global_connections(old_connections: list, new_connections: list, work_process: dict, restart_list: list,
    connect, cursor):
    for index, old_connect in enumerate(old_connections):
        if old_connect not in new_connections:
            ############################################################
            old_connections.pop(index)
            if old_connect in restart_list:
                restart_list.pop(restart_list.index(old_connect))
            status = stop_process(work_process[old_connect.name])
            if status:
                write_status_connect(cursor, connect, old_connect.name, False, False)
                del work_process[old_connect.name]
            ################
            # STOP PROCESS #
            ################
            ############################################################
    for index, new_connect in enumerate(new_connections):
        if new_connect not in old_connections:
            ############################################################
            old_connections.append(new_connect)
            proc, status, stop = start_process(new_connect)
            if proc:
                work_process[new_connect.name] = {
                    'process': proc,
                    'status': status,
                    'stop_point': stop
                }
            else:
                if new_connect not in restart_list:
                    restart_list.append(new_connect)
            #################
            # START PROCESS #
            #################
            ############################################################


def restart_process(restart_list, work_process):
    for index, connect in enumerate(restart_list):
        proc, status, stop = start_process(connect)
        if proc:
            work_process[connect['name']] = {
                'process': proc,
                'status': status,
                'stop_point': stop
            }
            restart_list.pop(index)


def write_status_connect(cursor, connect, name_connection, status_connect, status_process):
    cursor.execute(f"""
                        UPDATE connection_connection
                            SET status_connection={status_connect}
                                WHERE name='{name_connection}'
                    """)
    connect.commit()
    cursor.execute(f"""
                            UPDATE connection_connection
                                SET status_process={status_process}
                                    WHERE name='{name_connection}'
                        """)
    connect.commit()


def get_connection(cursor) -> list[ConnectionItem]:
    answer = []
    cursor.execute('''SELECT ip_address, port, name, driver, rack, slot, id FROM connection_connection 
                        WHERE switcher=true
    ''')
    for ip_address, port, name_con, driver, rack, slot, id_connection in cursor.fetchall():
        connection = ConnectionItem(
            name=name_con,
            ip=ip_address,
            port=port,
            driver=driver,
            area=[]
        )
        if driver == 'Snap7':
            connection.rack = rack
            connection.slot = slot
            connection.area = get_areas_for_connection_snap(cursor, id_con=id_connection)
        elif driver == 'ModbusTCP':
            connection.area = get_areas_for_connection_modbus(cursor, id_con=id_connection)
        else:
            connection.area = []
        answer.append(connection)
    return answer


def get_areas_for_connection_modbus(cursor, id_con: int) -> list[AreaItem]:
    areas = []
    cursor.execute(f'''SELECT id, name, slave_id, function, size, start_register FROM connection_area t WHERE 
                                connection_id = {id_con}''')
    for id_area, name_area, slave_id, function, size, start_register in cursor.fetchall():
        area_element = AreaItem(
            name=name_area,
            slave_id=slave_id,
            func=function,
            start_reg_adr=start_register,
            size=size,
            value_list=get_values_for_area_modbus(cursor, id_area=id_area)
        )
        areas.append(area_element)
    return areas


def get_values_for_area_modbus(cursor, id_area: int) -> list[ValueItem]:
    values = []
    cursor.execute(f'''SELECT id, start, name, type_value_get_data, type_value_write_data, if_change,
                            divide, divide_number, time_write_if_change, bit, signed, big_endian, byte_swap
                                            FROM connection_value WHERE area_id = {id_area}''')
    for (id_value, start, name_value, type_value_get_data, type_value_write_data, if_change, divide,
         divide_number, time_write_if_change, bit, signed, big_endian, byte_swap) in cursor.fetchall():
        value = ValueItem(
            name=name_value,
            start=start,
            type_val=type_value_get_data,
            type_table=type_value_write_data,
            if_change=if_change,
            divide=divide,
            divide_num=divide_number,
            min_time_check=time_write_if_change,
            bit=bit,
            signed=signed,
            big_or_little_endian=big_endian,
            byte_swap=byte_swap
        )
        values.append(value)
    return values


def get_areas_for_connection_snap(cursor, id_con: int) -> list[AreaItem]:
    areas = []
    cursor.execute(f'''SELECT id, name, type_area, number_db, start_byte, t.offset FROM connection_area t WHERE 
                                connection_id = {id_con}''')
    for id_area, name_area, type_area, number_db, start_byte, offset in cursor.fetchall():
        area_element = AreaItem(
            name=name_area,
            type_area=type_area,
            number_db=number_db,
            start_byte=start_byte,
            offset=offset,
            value_list=get_values_for_area_snap(cursor, id_area=id_area)
        )
        areas.append(area_element)
    return areas


def get_values_for_area_snap(cursor, id_area: int) -> list[ValueItem]:
    values = []
    cursor.execute(f'''SELECT id, start, name, type_value_get_data, type_value_write_data, if_change,
                                    divide, divide_number, time_write_if_change, bit 
                                            FROM connection_value WHERE area_id = {id_area}''')
    for (id_value, start, name_value, type_value_get_data, type_value_write_data, if_change, divide,
         divide_number, time_write_if_change, bit) in cursor.fetchall():
        value = ValueItem(
            name=name_value,
            start=start,
            type_val=type_value_get_data,
            type_table=type_value_write_data,
            if_change=if_change,
            divide=divide,
            divide_num=divide_number,
            min_time_check=time_write_if_change,
            bit=bit
        )
        values.append(value)
    return values
