import datetime
import struct
import threading
import time
from multiprocessing import Process
import cprint
import snap7
from snap7.util import get_bool
from pytz import timezone

from classType import AreaItem, ValueItem
from db_service import create_connection

tz = timezone('Europe/Minsk')

class ConnectSnapProcess(Process):
    def __init__(self, name_connect: str, ip: str, port: int, rack: int, slot: int, status: object, stop_point: object,
                 areas: list[AreaItem]):

        """
        TODO stop_point, ...
        """
        self.name_connect = name_connect
        self.address = ip
        self.status = status
        self.stop_point = stop_point
        self.rack = rack
        self.slot = slot
        self.port = port
        self.area_list = areas
        self.bind = {}
        self.error_read_data = False
        self.bytearray_data = {}  # bytearray()
        self.values = {}
        self._conn, self._c = create_connection()
        self.client = snap7.client.Client()
        self.client.set_connection_type(3)
        try:
            self.client.connect(self.address, self.rack, self.slot, tcpport=self.port)
        except:
            cprint.cprint.err("NotConnect to PLC")
        super(ConnectSnapProcess, self).__init__()

    def __get_db_data(self, area: AreaItem) -> bool:
        """
        Get data from PLC that bytearray type
        """
        try:
            if area.name not in self.bytearray_data:
                self.bytearray_data[area.name] = bytearray()
            if area.type_area == 'DB':
                self.bytearray_data[area.name] = self.client.db_read(area.number_db, area.start_byte, area.offset)
                self.status.value = True
                return True
            elif area.type_area == 'PA':
                self.bytearray_data[area.name] = self.client.read_area(snap7.types.areas['PA'], 0, area.start_byte,
                                                                       area.offset)
                self.status.value = True
                return True
            else:
                return False
        except:
            self.status.value = False
            self.error_read_data = True
            return False

    def __reconnect_to_plc(self) -> bool:
        """
        Reconnect to PLC
        """
        cprint.cprint.warn("Connect to PLC %s" % self.address)
        self.client.destroy()
        try:
            self.client = snap7.client.Client()
            self.client.set_connection_type(3)
            self.client.connect(self.address, self.rack, self.slot, tcpport=self.port)
            self.status.value = True
            cprint.cprint.info("Good connect to %s" % self.address)
            return True
        except:
            time.sleep(3)
            return False

    def __create_table_if_not_exist(self) -> None:
        """
        Create table in DB if that not exist
        """
        cprint.cprint.info("Create table")
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
            self.values[f'write_time_{table_name}'] = val[1]
        print(f'create and set table sh_{table_name}')

    def __parse_bytearray(self, param_value: ValueItem, area_name: str) -> any:
        """
        Get variable from bytearray and reform to needed type
        """
        start = param_value.start
        match param_value.type_val:
            case 'int':
                offset = 2
                end = start + offset
                result = disassemble_int(self.bytearray_data[area_name][start:end])
                if param_value.divide:
                    if result > 65000:
                        result = 0
                    else:
                        result = result / param_value.divide_num
            case 'float':
                offset = 4
                end = start + offset
                result = disassemble_float(self.bytearray_data[area_name][start:end])
            case 'double':
                offset = 4
                end = start + offset
                result = disassemble_double(self.bytearray_data[area_name][start:end])
            case 'bool':
                end = start + 1
                result = from_bytearray_to_bit(data=self.bytearray_data[start:end], bit=param_value.bit)
            case _:
                result = 0
        return result

    def __write_to_db(self, table_name, value) -> None:
        """
        Write variable to DB
        """
        self._c.execute('''INSERT INTO sh_''' + table_name + ''' (value) VALUES (''' + str(value) + ''');''')

    def _thread_for_write_data(self, value_param: ValueItem, area_name):
        value = self.__parse_bytearray(value_param, area_name)
        now = current_time()
        timeout_sec = value_param.min_time_check
        if value_param.if_change and value_param.name not in self.values:
            cprint.cprint.info("create last value in %s " % value_param.name)
            self.values[value_param.name] = value
            self.__write_to_db(table_name=value_param.name, value=value)
            self.values[f'write_time_{value_param.name}'] = current_time()

        if value_param.if_change and self.values[value_param.name] != value and \
                (now-self.values[f'write_time_{value_param.name}']).microseconds/1000 > timeout_sec:
            self.values[value_param.name] = value
            self.__write_to_db(table_name=value_param.name, value=value)
            self.values[f'write_time_{value_param.name}'] = current_time()

        if not value_param.if_change:
            if f'write_time_{value_param.name}' not in self.values:
                self.__write_to_db(table_name=value_param.name, value=value)
                self.values[f'write_time_{value_param.name}'] = current_time()
            elif (now - self.values[f'write_time_{value_param.name}']).microseconds/1000 > timeout_sec:
                self.__write_to_db(table_name=value_param.name, value=value)
                self.values[f'write_time_{value_param.name}'] = current_time()

    def run(self):
        self.__create_table_if_not_exist()
        while True:
            for area in self.area_list:
                if not self.__get_db_data(area):
                    self.__reconnect_to_plc()
                else:
                    threads = list()
                    for value in area.value_list:
                        thread = threading.Thread(target=self._thread_for_write_data, args=(value, area.name))
                        threads.append(thread)
                        while threading.active_count() > 250:
                            time.sleep(0.01)
                        thread.start()
                    for thread in threads:
                        thread.join()
                    self._conn.commit()


def disassemble_int(data) -> int:
    """
    Transform bytearray to int type
    """
    return int.from_bytes(data, "big", signed=True)


def disassemble_float(data) -> float:
    """
    Transform bytearray to float type
    """
    val = struct.unpack('>f', data)
    return round(val[0], 1)


def disassemble_double(data) -> int:
    """
    Transform bytearray 'double' to int(bigint) type
    """
    val = struct.unpack('>d', data)
    return val[0]


def from_bytearray_to_bit(bit, data) -> int:
    try:
        result = get_bool(data, 0, bit)
    except:
        result = 0
    return int(result)


def current_time() -> datetime.datetime:
    return datetime.datetime.now(tz)
