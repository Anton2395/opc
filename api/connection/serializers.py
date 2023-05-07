from connection.models import Connection, Area, Value
from rest_framework import serializers
import time


class ValueSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Value
        fields = ['id', 'start', 'name', 'type_value_get_data', 'type_value_write_data', 'if_change', 'divide',
                  'divide_number', 'time_write_if_change', 'bit', 'area_id', 'area']


class ValueSimpleSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Value
        fields = ['id', 'start', 'name', 'type_value_get_data', 'type_value_write_data', 'if_change', 'divide',
                  'divide_number', 'time_write_if_change', 'bit']


class AreaSerializer(serializers.HyperlinkedModelSerializer):
    value = ValueSerializer(many=True, read_only=True)

    class Meta:
        model = Area
        fields = ["id", "name", "type_area", "number_db", "start_byte", "offset", "connection", "connection_id",
                  "value"]


class ConnectionSerializer(serializers.HyperlinkedModelSerializer):
    # area = AreaSerializer(many=True, read_only=True)
    class Meta:
        model = Connection
        fields = ["id", "name", "driver", "ip_addres", "port", "slot", "rack", "switcher", "status_conncection",
                  "status_proccese"]


class AreaSimpleSerializer(serializers.ModelSerializer):
    value = ValueSimpleSerializer(many=True, read_only=True)
    class Meta:
        model = Area
        fields = ["id", "name", "type_area", "number_db", "start_byte", "offset", "connection_id", "value"]
