from django.db.models import F, Sum, Window
from django_filters.views import FilterView

from .filters import CurrentTotalFilter, MonthlyTimelineFilter
from .models import CurrentTotal, MonthlyTimeline


class MonthlyTimelineView(FilterView):
    context_object_name = "monthly_timeline"
    filterset_class = MonthlyTimelineFilter

    queryset = MonthlyTimeline.objects.annotate(
        net_sum=Window(
            expression=Sum(F("net_nominal_capacity")),
            # to seperate by energey_source use: partition_by=[F("energy_source")],
            order_by=["date"],
        )
    ).distinct(
        "date",
        # see above: "energy_source"
    )

    template_name = "energy_sources/timeline.html"


monthly_timeline_view = MonthlyTimelineView.as_view()


class CurrentTotalView(FilterView):
    context_object_name = "current_total"
    filterset_class = CurrentTotalFilter

    queryset = CurrentTotal.objects.all()

    template_name = "energy_sources/current_total.html"


current_total_view = CurrentTotalView.as_view()
