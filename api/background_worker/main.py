import psycopg2


def create_connection():
    conn = psycopg2.connect(dbname='postgres', user='mvlab', password='z1x2c3', host='127.0.0.1', port=5432)
    cursor = conn.cursor()
    return conn, cursor


def get_connection(cursor) -> list:
    answer = []
    cursor.execute('''SELECT DISTINCT ip_address, port, name, driver, id FROM connection_connection''')
    for ip_address, port, name_con, driver, id_connection in cursor.fetchall():
        response_temp = {
            'name': name_con,
            'ip': ip_address,
            'port': port,
            'area': [],
            'driver': driver
        }
        if driver == 'Snap7':
            cursor.execute(f'''SELECT id, name, type_area, number_db, start_byte, t.offset FROM connection_area t WHERE 
                            connection_id = {id_connection}''')
            for id_area, name_area, type_area, number_db, start_byte, offset in cursor.fetchall():
                area_element = {
                    'name': name_area,
                    'type_area': type_area,
                    'number_db': number_db,
                    'start_byte': start_byte,
                    'offset': offset,
                    'value_list': []
                }
                cursor.execute(f'''SELECT id, start, name, type_value_get_data, type_value_write_data, if_change,
                                divide, divide_number, time_write_if_change, bit 
                                        FROM connection_value WHERE area_id = {id_area}''')
                for (id_value, start, name_value, type_value_get_data, type_value_write_data, if_change, divide,
                     divide_number, time_write_if_change, bit) in cursor.fetchall():
                    area_element['value_list'].append({
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
                response_temp['area'].append(area_element)
        answer.append(response_temp)
    return answer


conn_db, cursor_db = create_connection()
print(get_connection(cursor=cursor_db))
conn_db.close()
