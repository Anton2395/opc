from connection.models import Connection, Area, Value
from rest_framework import serializers
import time


class ValueSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Value
        fields = ['id', 'start', 'name', 'type_value_get_data', 'type_value_write_data', 'if_change', 'divide',
                  'divide_number', 'time_write_if_change', 'bit', 'area_id', 'area', 'byte_swap', 'big_endian',
                  'signed']


class ValueSimpleSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Value
        fields = ['id', 'start', 'name', 'type_value_get_data', 'type_value_write_data', 'if_change', 'divide',
                  'divide_number', 'time_write_if_change', 'bit', 'signed', 'big_endian', 'byte_swap']


class AreaSerializer(serializers.HyperlinkedModelSerializer):
    value = ValueSerializer(many=True, read_only=True)

    class Meta:
        model = Area
        fields = ["id", "name", "type_area", "number_db", "start_byte", "offset", "connection", "connection_id",
                  "value", "slave_id", "function", "size", "start_register"]


class ConnectionSerializer(serializers.HyperlinkedModelSerializer):
    # area = AreaSerializer(many=True, read_only=True)
    class Meta:
        model = Connection
        fields = ["id", "name", "driver", "ip_address", "port", "slot", "rack", "switcher", "status_connection",
                  "status_process"]


class AreaSimpleSerializer(serializers.ModelSerializer):
    value = ValueSimpleSerializer(many=True, read_only=True)
    class Meta:
        model = Area
        fields = ["id", "name", "type_area", "number_db", "start_byte", "offset", "connection_id", "value", "slave_id",
                  "function", "size", "start_register"]
