from django.urls import path

from .views import energy_sources_list_view

app_name = "energy_sources"
urlpatterns = [
    path("", energy_sources_list_view, name="list"),
]
