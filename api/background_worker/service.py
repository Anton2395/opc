import psycopg2


def create_connection():
    conn = psycopg2.connect(dbname='postgres', user='mvlab', password='z1x2c3', host='127.0.0.1', port=5432)
    cursor = conn.cursor()
    return conn, cursor


def get_connection(cursor) -> list:
    answer = []
    cursor.execute('''SELECT ip_address, port, name, driver, rack, slot, id FROM connection_connection''')
    for ip_address, port, name_con, driver, rack, slot, id_connection in cursor.fetchall():
        response_temp = {
            'name': name_con,
            'ip': ip_address,
            'port': port,
            'driver': driver
        }
        if driver == 'Snap7':
            response_temp['rack'] = rack
            response_temp['slot'] = slot
            response_temp['area'] = get_areas_for_connection_snap(cursor, id_con=id_connection)
        elif driver == 'ModbusTCP':
            response_temp['area'] = get_areas_for_connection_modbus(cursor, id_con=id_connection)
        else:
            response_temp['area'] = []
        answer.append(response_temp)
    return answer


def get_areas_for_connection_modbus(cursor, id_con: int) -> list:
    areas = []
    cursor.execute(f'''SELECT id, name, slave_id, function, size, start_register FROM connection_area t WHERE 
                                connection_id = {id_con}''')
    for id_area, name_area, slave_id, function, size, start_register in cursor.fetchall():
        area_element = {
            'name': name_area,
            'slave_id': slave_id,
            'func': function,
            'start_reg_adr': size,
            'size': start_register,
            'value_list': get_values_for_area_modbus(cursor, id_area=id_area)
        }
        areas.append(area_element)
    return areas


def get_values_for_area_modbus(cursor, id_area: int) -> list:
    values = []
    cursor.execute(f'''SELECT id, start, name, type_value_get_data, type_value_write_data, if_change,
                            divide, divide_number, time_write_if_change, bit, signed, big_endian, byte_swap
                                            FROM connection_value WHERE area_id = {id_area}''')
    for (id_value, start, name_value, type_value_get_data, type_value_write_data, if_change, divide,
         divide_number, time_write_if_change, bit, signed, big_endian, byte_swap) in cursor.fetchall():
        values.append({
            'name': name_value,
            'start': start,
            'type_val': type_value_get_data,
            'type_table': type_value_write_data,
            'if_change': if_change,
            'divide': divide,
            'divide_num': divide_number,
            'min_time_check': time_write_if_change,
            'bit': bit,
            "signed": signed,
            "big_or_little_endian": big_endian,
            "byte_swap": byte_swap
            # "max_time_check": 1,
        })
    return values


def get_areas_for_connection_snap(cursor, id_con: int) -> list:
    areas = []
    cursor.execute(f'''SELECT id, name, type_area, number_db, start_byte, t.offset FROM connection_area t WHERE 
                                connection_id = {id_con}''')
    for id_area, name_area, type_area, number_db, start_byte, offset in cursor.fetchall():
        area_element = {
            'name': name_area,
            'type_area': type_area,
            'number_db': number_db,
            'start_byte': start_byte,
            'offset': offset,
            'value_list': get_values_for_area_snap(cursor, id_area=id_area)
        }
        areas.append(area_element)
    return areas


def get_values_for_area_snap(cursor, id_area: int) -> list:
    values = []
    cursor.execute(f'''SELECT id, start, name, type_value_get_data, type_value_write_data, if_change,
                                    divide, divide_number, time_write_if_change, bit 
                                            FROM connection_value WHERE area_id = {id_area}''')
    for (id_value, start, name_value, type_value_get_data, type_value_write_data, if_change, divide,
         divide_number, time_write_if_change, bit) in cursor.fetchall():
        values.append({
            'name': name_value,
            'start': start,
            'type_value_get_data': type_value_get_data,
            'type_value_write_data': type_value_write_data,
            'if_change': if_change,
            'divide': divide,
            'divide_number': divide_number,
            'time_write_if_change': time_write_if_change,
            'bit': bit
        })
    return values
