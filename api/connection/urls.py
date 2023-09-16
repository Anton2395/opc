from django.urls import path
from connection.views import ConnectionViewSet, AreaViewSet, AreaConnectionSet, ValueViewSet, ConnectionStatus, \
    ChartPoint, CheckName
from rest_framework import routers

router = routers.DefaultRouter()
router.register(r'connection', ConnectionViewSet)
router.register(r'area', AreaViewSet)
router.register(r'value', ValueViewSet)

urlpatterns = [
    path('<int:pk>/area', AreaConnectionSet.as_view()),
    path('status/', ConnectionStatus.as_view()),
    path('get_point/', ChartPoint.as_view()),
    path('check_name/', CheckName.as_view())
    # path('', ConnectionViewSet.as_view(), name="Con"),
    # path('/<int:pk>', ConnectionViewSet.as_view(), name="Connections"),
]