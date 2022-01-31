from django.contrib import admin
from django.urls import path

from . import views

urlpatterns = [
    path("get_csrf_token", views.get_csrf_token, name="get_csrf_token"),
    path("login", views.login, name="login"),
    path("logout", views.logout, name="logout"),
    path("register", views.register, name="register"),
    path("get_user", views.GetUser.as_view(), name="get_user"),
    #
    path("video_upload", views.VideoUpload.as_view(), name="video_upload"),
    path("video_list", views.VideoList.as_view(), name="video_list"),
    path("video_get", views.VideoGet.as_view(), name="video_get"),
    path("video_delete", views.VideoDelete.as_view(), name="video_delete"),
]
