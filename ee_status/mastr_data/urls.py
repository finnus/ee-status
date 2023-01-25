from django.urls import path

from .views import energy_units_view, rankings_view, search_view, totals_view

app_name = "mastr_data"
urlpatterns = [
    path("", search_view, name="search"),
    path("totals", totals_view, name="totals"),
    path("rankings", rankings_view, name="rankings"),
    path("units", energy_units_view, name="energy_units"),
]
