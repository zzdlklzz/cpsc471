from django.urls import path

from . import views

urlpatterns = [
    path("registrations", views.registration_list),
    path("registrations/<int:registration_id>", views.registration_detail,),
]