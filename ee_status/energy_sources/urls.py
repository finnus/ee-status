from django.urls import path

from .views import monthly_timeline_view

app_name = "energy_sources"
urlpatterns = [
    path("timeline", monthly_timeline_view, name="timeline"),
]
