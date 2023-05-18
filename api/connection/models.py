from django.db import models


class Connection(models.Model):
    name = models.CharField(max_length=100, null=False)
    driver = models.CharField(max_length=30, null=False)
    ip_address = models.CharField(max_length=17, null=False)
    port = models.IntegerField(default=502, null=False)
    slot = models.IntegerField(null=True)
    rack = models.IntegerField(null=True)
    switcher = models.BooleanField(null=False, default=False)
    status_connection = models.BooleanField(null=False, default=False)
    status_process = models.BooleanField(null=False, default=False)


class Area(models.Model):
    name = models.CharField(max_length=100, null=False)
    # Snap 7
    type_area = models.CharField(max_length=5, null=True)
    number_db = models.IntegerField(default=None, null=True)
    start_byte = models.IntegerField(default=0, null=True)
    offset = models.IntegerField(default=1, null=True)
    # Modbus TCP
    slave_id = models.IntegerField(default=1, null=False)
    function = models.IntegerField(default=0, null=False)
    size = models.IntegerField(default=0, null=False)
    start_register = models.IntegerField(default=0, null=False)

    connection = models.ForeignKey(Connection, on_delete=models.CASCADE, related_name='area')


class Value(models.Model):
    start = models.IntegerField(null=False)
    name = models.CharField(max_length=100, null=False)
    type_value_get_data = models.CharField(max_length=10, null=False)
    type_value_write_data = models.CharField(max_length=10, null=False)
    if_change = models.BooleanField(null=False, default=True)
    divide = models.BooleanField(null=False, default=False)
    divide_number = models.FloatField(default=1)
    bit = models.IntegerField(null=True)
    time_write_if_change = models.IntegerField(default=1000)
    # Modbus TCP
    signed = models.BooleanField(default=False, null=False)
    big_endian = models.BooleanField(default=False, null=False)
    byte_swap = models.BooleanField(default=True, null=False)

    area = models.ForeignKey(Area, on_delete=models.CASCADE, related_name='value')
