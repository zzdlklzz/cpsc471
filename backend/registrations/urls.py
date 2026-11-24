from django.urls import path

from . import views

urlpatterns = [
    path("shelters", views.shelter_list),
    path("registrations", views.registration_list),
    path("registrations/<int:registration_id>", views.registration_detail,),
]