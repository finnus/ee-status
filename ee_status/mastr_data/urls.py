from django.urls import path

from .views import totals_view

app_name = "mastr_data"
urlpatterns = [
    path("totals", totals_view, name="totals"),
]
