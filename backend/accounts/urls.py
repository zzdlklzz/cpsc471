from django.urls import path

from . import views

urlpatterns = [
    path("auth/csrf", views.csrf),
    path("auth/login", views.login),
    path("auth/logout", views.logout),
    path("auth/me", views.me),
    path("auth/signup", views.signup),
    path("zones", views.zones),
    path("household", views.household),
    path("household/members", views.members),
    path("household/members/<int:member_id>", views.member_detail),
    path("household/members/<int:member_id>/account", views.member_account),
]
