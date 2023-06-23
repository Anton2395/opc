from dataclasses import dataclass


@dataclass
class ValueItem:
    name: str
    start: int
    type_val: str
    type_table: str
    if_change: bool
    divide: bool
    divide_num: float
    min_time_check: int
    bit: int
    signed: bool = None
    big_or_little_endian: bool = None
    byte_swap: bool = None


@dataclass
class AreaItem:
    name: str
    value_list: list[ValueItem]
    slave_id: int = None
    func: int = None
    start_reg_adr: int = None
    size: int = None
    type_area: str = None
    number_db: int = None
    start_byte: int = None
    offset: int = None


@dataclass
class ConnectionItem:
    name: str
    ip: str
    port: int
    driver: str
    area: list[AreaItem]
    rack: int = None
    slot: int = None