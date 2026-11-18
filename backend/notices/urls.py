from django.urls import path

from . import views

urlpatterns = [
    path("events", views.events),
    path("notices", views.notice_list),
    path("notices/<int:notice_id>", views.notice_detail),
]
