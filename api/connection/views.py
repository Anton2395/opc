from rest_framework.viewsets import ModelViewSet, ViewSet, generics
from rest_framework import permissions
from connection.models import Connection, Area, Value
from connection.serializers import ConnectionSerializer, AreaSerializer, AreaSimpleSerializer, ValueSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
import time

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


class ValueViewSet(ModelViewSet):
    queryset = Value.objects.all().order_by('pk')
    serializer_class = ValueSerializer
