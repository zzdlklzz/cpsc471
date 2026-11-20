from django.urls import path

from . import views

urlpatterns = [
    path("auth/login", views.login),
    path("events", views.events),
    path("events/<int:event_id>", views.event_detail),
]
