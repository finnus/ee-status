from django.db.models import F, Sum, Window
from django_filters.views import FilterView

from .filters import MonthlyTimelineFilter
from .models import MonthlyTimeline


class MonthlyTimelineView(FilterView):
    context_object_name = "monthly_timeline"
    filterset_class = MonthlyTimelineFilter

    queryset = MonthlyTimeline.objects.annotate(
        net_sum=Window(expression=Sum(F("net_nominal_capacity")), order_by=["date"])
    ).distinct("date")

    template_name = "energy_sources/timeline.html"


monthly_timeline_view = MonthlyTimelineView.as_view()
