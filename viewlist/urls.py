from django.urls import path
from . import views

urlpatterns = [
    path("", views.all_violations_list, name="all_violations_list"),
]
