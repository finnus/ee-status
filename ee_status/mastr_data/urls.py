from django.urls import path

from .views import energyunits_list_view, rankings_view, search_view, totals_view

app_name = "mastr_data"
urlpatterns = [
    path("", search_view, name="search"),
    path("totals", totals_view, name="totals"),
    path("rankings", rankings_view, name="rankings"),
    path("units", energyunits_list_view, name="energy_units"),
]
