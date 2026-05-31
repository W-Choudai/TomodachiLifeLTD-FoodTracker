from django.urls import path
from . import views

app_name = "tomodachi"

urlpatterns = [
    path("", views.index, name="index"),
    path("mii/<int:mii_id>/", views.mii_detail, name="mii_detail"),
    path("mii/add/", views.add_mii, name="add_mii"),
    path("mii/<int:mii_id>/delete/", views.delete_mii, name="delete_mii"),
    path("mii/<int:mii_id>/preference/", views.set_preference, name="set_preference"),
]