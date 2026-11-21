from django.urls import path

from . import views

urlpatterns = [
    path("auth/login", views.login),
    path("events", views.events),
    path("events/<int:event_id>", views.event_detail),
    path("notices", views.notices),
    path("notices/<int:notice_id>", views.notice_detail),
]
