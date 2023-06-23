from rest_framework.viewsets import ModelViewSet, ViewSet, generics
from rest_framework import permissions
from django.db import connection
from connection.models import Connection, Area, Value
from connection.serializers import ConnectionSerializer, AreaSerializer, AreaSimpleSerializer, ValueSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
import datetime
from pytz import timezone

tz = timezone('Europe/Minsk')


class ConnectionViewSet(ModelViewSet):
    queryset = Connection.objects.all().order_by('pk')
    serializer_class = ConnectionSerializer
    # permission_classes = [permissions.IsAuthenticated]


class AreaViewSet(ModelViewSet):
    queryset = Area.objects.all().order_by('pk')
    serializer_class = AreaSerializer
    # permission_classes = [permissions.IsAuthenticated]


class AreaConnectionSet(APIView):
    def get(self, request, pk):
        areas = Area.objects.filter(connection=pk).order_by('pk')
        serializer = AreaSimpleSerializer(areas, many=True)
        return Response(serializer.data)


class ConnectionStatus(APIView):
    def get(self, request):
        connections = Connection.objects.all()
        response = {}
        for connect in connections:
            response[connect.id] = {
                'status_connection': connect.status_connection,
                'switcher': connect.switcher,
                'status_process': connect.status_process,
            }
        return Response(response)

    def post(self, request):
        connect = Connection.objects.get(pk=request.data['id'])
        if connect.switcher:
            connect.switcher = False
        else:
            connect.switcher = True
        connect.save()
        return Response('done')


class ValueViewSet(ModelViewSet):
    queryset = Value.objects.all().order_by('pk')
    serializer_class = ValueSerializer


class ChartPoint(APIView):
    def post(self, request):
        value = Value.objects.get(pk=request.data['id_variable'])
        table_name = 'sh_' + value.area.connection.name + '_' + value.area.name + '_' + value.name
        with connection.cursor() as cursor:
            if 'last_time' in request.data.keys():
                date_conv = datetime.datetime.fromtimestamp(request.data['last_time'])
                print(date_conv)
                date_tz = tz.localize(date_conv)
                print(date_tz)
                cursor.execute(
                    f"""SELECT date_part('epoch', now_time)*1000, value
                            FROM {table_name}
                                WHERE now_time>'{date_tz}'
                                    ORDER by now_time""")
                answer = cursor.fetchall()
            else:
                cursor.execute(f"""SELECT date_part('epoch', now_time)*1000, value
                                        FROM {table_name}
                                            ORDER by now_time DESC LIMIT 100""")
                answer = cursor.fetchall()

                answer.reverse()
        return Response(answer)
