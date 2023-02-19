from django.urls import path, include

from users.views import CustomAuthToken, Logout, UserInfo

urlpatterns = [
    path('login/', CustomAuthToken.as_view(), name="login_link"),
    path('logout/', Logout.as_view()),
    path('info/', UserInfo.as_view())
]