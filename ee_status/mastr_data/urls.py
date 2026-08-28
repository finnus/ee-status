from django.urls import path

from .views import rankings_view
from .views import search_municipality
from .views import search_view
from .views import totals_view

app_name = "mastr_data"
urlpatterns = [
    path("", search_view, name="search"),
    path("totals", totals_view, name="totals"),
    path("rankings", rankings_view, name="rankings"),
]

htmx_urlpatterns = [
    path("search-municipality/", search_municipality, name="search-municipality"),
]

urlpatterns += htmx_urlpatterns
