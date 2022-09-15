from django.urls import path

from .views import current_total_view, monthly_timeline_view

app_name = "mastr_data"
urlpatterns = [
    path("timeline", monthly_timeline_view, name="timeline"),
    path("totals", current_total_view, name="totals"),
]
