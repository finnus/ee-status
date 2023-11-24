from django.urls import path

from .views import multi_polygon_map, rankings_view, search_view, totals_view

app_name = "mastr_data"
urlpatterns = [
    path("", search_view, name="search"),
    path("totals", totals_view, name="totals"),
    path("rankings", rankings_view, name="rankings"),
    path("multi_polygon_map/", multi_polygon_map, name="multi_polygon_map"),
]
