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
    #
    path("analyser_list", views.AnalyserList.as_view(), name="analyser_list"),
    #
    path("timeline_list", views.TimelineList.as_view(), name="timeline_list"),
    path("timeline_duplicate", views.TimelineDuplicate.as_view(), name="timeline_duplicate"),
    path("timeline_rename", views.TimelineRename.as_view(), name="timeline_rename"),
    path("timeline_delete", views.TimelineDelete.as_view(), name="timeline_delete"),
    #
    path("timeline_segment_list", views.TimelineSegmentList.as_view(), name="timeline_segment_list"),
    #
    path(
        "timeline_segment_annotation_list",
        views.TimelineSegmentAnnoatationList.as_view(),
        name="timeline_segment_annotation_list",
    ),
    path(
        "timeline_segment_annotation_create",
        views.TimelineSegmentAnnoatationCreate.as_view(),
        name="timeline_segment_annotation_create",
    ),
    #
    path("annotation_category_create", views.AnnoatationCategoryCreate.as_view(), name="annotation_category_create"),
    path("annotation_category_list", views.AnnoatationCategoryList.as_view(), name="annotation_category_list"),
]
