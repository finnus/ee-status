from django.urls import path

from .views import rankings_view, totals_view

app_name = "mastr_data"
urlpatterns = [
    path("totals", totals_view, name="totals"),
    path("rankings", rankings_view, name="rankings"),
]
