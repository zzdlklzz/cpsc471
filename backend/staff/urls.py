from django.urls import path

from . import views

urlpatterns = [
    path("registrations", views.registrations),
    path("registrations/<int:registration_id>", views.registration_detail),
    path("shelters/<int:shelter_id>/placements", views.shelter_placements),
    path("auth/login", views.login),
    path("events", views.events),
    path("events/<int:event_id>", views.event_detail),
    path("notices", views.notices),
    path("notices/<int:notice_id>", views.notice_detail),
]
