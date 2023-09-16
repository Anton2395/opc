import datetime
import struct
import threading
import time
from multiprocessing import Process

import modbus_tk.defines as cst
import modbus_tk.modbus_tcp as modbus_tcp
import pytz

from db_service import create_connection
from classType import AreaItem, ValueItem


class ConnectModProcess(Process):
    def __init__(self, name_connect: str, ip: str, port: int, status: object, stop_point: object, areas: list[AreaItem]):
        """
        TODO normal comment
        """
        self.name_connect = name_connect
        self.ip = ip
        self.status = status
        self.stop_point = stop_point
        self.port = port
        self.area_list = areas
        self.bytearray_data = {}
        self.values = {}
        self._conn, self._c = create_connection()
        
        self.master = modbus_tcp.TcpMaster(
            host=ip,
            port=port,
            timeout_in_sec=1
        )
        try:
            self.master._do_open()
            self.status.value = True
        except ConnectionResetError:
            self.status.value = False
        except TimeoutError:
            self.status.value = False
        super(ConnectModProcess, self).__init__()
    
    def __create_table_if_not_exist(self):
        """Создание таблиц для хранения данных (если их нету)"""
        for area in self.area_list:
            for value in area.value_list:
                match value.type_table:
                    case 'int':
                        type_column = 'INT'
                    case 'float':
                        type_column = 'REAL'
                    case 'double':
                        type_column = 'BIGINT'
                    case 'bool':
                        type_column = 'INT'
                    case _:
                        type_column = 'INT'
                value.name = self.name_connect + '_' + area.name + '_' + value.name
                self._c.execute('''CREATE TABLE IF NOT EXISTS sh_''' + value.name + ''' \
                                (id serial primary key,now_time TIMESTAMP  WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, \
                                value ''' + type_column + ''')''')
                self._conn.commit()
                self.set_old_value(value.name)

    def set_old_value(self, table_name):
        self._c.execute(f'''
                        SELECT value, now_time
                            FROM sh_{table_name}
                            ORDER BY now_time DESC
                            LIMIT 1
                        ''')
        val = self._c.fetchone()
        if val:
            self.values[table_name] = val[0]
            self.values["time_"+table_name] = val[1].replace(tzinfo=None)
        print(f'create and set table mvlab_{table_name}')

    def __get_data(self, area: AreaItem):
        """
        Получение данных с устройства
        """
        
        try:
            if area.name not in self.bytearray_data:
                self.bytearray_data[area.name] = []
            if area.func == 3:
                self.bytearray_data[area.name] = self.master.execute(area.slave_id, cst.READ_HOLDING_REGISTERS,
                                                                     area.start_reg_adr, area.size)
                return True
            elif area.func == 4:
                self.bytearray_data[area.name] = self.master.execute(area.slave_id, cst.READ_INPUT_REGISTERS,
                                                                     area.start_reg_adr, area.size)
                return True
            else:
                return False
        except Exception as e:
            print("Can't get data from PLC. Text error: ", self.name_connect)
            print(e)
            self.master._do_open()
            return False
    
    def __parse_bytearray(self, param_value: ValueItem, area_name: str):
        type_val = param_value.type_val
        start = param_value.start
        if type_val == 'int':
            temp_result = self.bytearray_data[area_name][start]
            result = convert_to_int(param_value, temp_result)
        elif type_val == 'float':
            end = start + 2
            temp_result = self.bytearray_data[area_name][start:end]
            result = convert_to_float(param_value, temp_result)
        elif type_val == 'double':
            end = start + 2
            temp_result = self.bytearray_data[area_name][start:end]
            result = convert_to_double(param_value, temp_result)
        elif type_val == 'bool':
            end = start + 2
            temp_result = self.bytearray_data[area_name][start:end]
            bits_mask_decimal = convert_to_double(param_value, temp_result)
            result = convert_to_bool(bits_mask_decimal, param_value.bit)
        else:
            print('Bad choice type value')
            result = False
        return result
    
    def __thread_for_write_data(self, value_param: ValueItem, area_name: str):
        """
        
        """
        value = self.__parse_bytearray(value_param, area_name)
        now = datetime.datetime.now()
        min_time_check = value_param.min_time_check

        if value_param.if_change and value_param.name not in self.values:
            self.values[value_param.name] = value
            self.values["time_"+value_param.name] = now
            self.__write_to_db(value_param.name, value)
            
        if value_param.if_change and value_param.name in self.values and "time_" + value_param.name in self.values:
            if value != self.values[value_param.name]:
                if round((now - self.values['time_'+value_param.name]).total_seconds()*1000) >= min_time_check:
                    self.values[value_param.name] = value
                    self.values["time_"+value_param.name] = now
                    self.__write_to_db(value_param.name, value)
        
        if not value_param.if_change and "time_" + value_param.name not in self.values:
            self.values["time_"+value_param.name] = now
            self.__write_to_db(value_param.name, value)

        if not value_param.if_change and "time_" + value_param.name in self.values:
            if round((now - self.values['time_'+value_param.name]).total_seconds()*1000) >= min_time_check:
                self.values["time_"+value_param.name] = now
                self.__write_to_db(value_param.name, value)

    def __write_to_db(self, tablename, value):
        """Запись распаршеных данных в БД"""
        self._c.execute(
            f'''INSERT INTO sh_{tablename} (value) VALUES ({value});''')

    def run(self):
        self.__create_table_if_not_exist()  # создание таблиц если их нет
        while True:
            try:
                if self.stop_point.value:
                    break
                for area in self.area_list:
                    if not self.__get_data(area):
                        self.status.value = False
                    else:
                        threads = list()
                        for value in area.value_list:
                            data_get_process = threading.Thread(target=self.__thread_for_write_data,
                                                                args=(value, area.name))
                            threads.append(data_get_process)
                            while threading.active_count() > 250:
                                time.sleep(0.01)
                            data_get_process.start()
                        self.status.value = True
                        for thread in threads:
                            thread.join()
                        self._conn.commit()
            except:
                self.status.value = False
        self.stop_point.value = False


def convert_to_int(value: ValueItem, data):
    if value.byte_swap:
        convert = struct.pack('>H', data)
    else:
        convert = struct.pack('H', data)
    if value.signed:
        result = struct.unpack('h', convert)[0]
    else:
        result = struct.unpack('H', convert)[0]
    if value.divide:
        result = result / value.divide_num
    return result


def convert_to_float(value: ValueItem, data):
    if value.byte_swap:
        convert_to_byte = struct.pack('>H', data[1]) + struct.pack('>H', data[0])
    else:
        convert_to_byte = struct.pack('HH', data[1], data[0])
    if value.big_or_little_endian:
        result = struct.unpack('f', convert_to_byte)[0]
    else:
        result = struct.unpack('>f', convert_to_byte)[0]
    if value.divide:
        result = result / value.divide_num
    return result


def convert_to_double(value: ValueItem, data):
    if value.byte_swap:
        convert = struct.pack('>H', data[1]) + struct.pack('>H', data[0])
    else:
        convert = struct.pack('HH', data[1], data[0])
    if value.signed:
        if value.big_or_little_endian:
            result = struct.unpack('<l', convert)[0]
        else:
            result = struct.unpack('>l', convert)[0]
    else:
        if value.big_or_little_endian:
            result = struct.unpack('<L', convert)[0]
        else:
            result = struct.unpack('>L', convert)[0]
    if value.divide:
        result = result / value.divide_num
    return result


def convert_to_bool(data, bit):
    bit_mask = f"{data:032b}"[::-1]
    result = int(bit_mask[bit])
    return result
