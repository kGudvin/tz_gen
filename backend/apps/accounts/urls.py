from django.urls import path

from apps.accounts.views import login, me, register

urlpatterns = [
    path("register/", register, name="register"),
    path("login/", login, name="login"),
    path("me/", me, name="me"),
]

