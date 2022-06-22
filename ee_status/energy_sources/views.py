from django.db.models import F, Sum, Window
from django.db.models.functions.datetime import TruncMonth
from django_filters.views import FilterView

from .filters import SolarExtendedFilter
from .models import SolarExtended


class SolarExtendedListView(FilterView):
    context_object_name = "solar_extended_list"
    filterset_class = SolarExtendedFilter

    queryset = (
        SolarExtended.objects.annotate(month=TruncMonth("inbetriebnahmedatum"))
        .values("month")
        .distinct("month")
        .annotate(
            net_sum=Window(
                Sum(F("nettonennleistung")), order_by=F("inbetriebnahmedatum").asc()
            )
        )
        .values("month", "net_sum")
    )

    template_name = "energy_sources/solar_extended_list.html"


energy_sources_list_view = SolarExtendedListView.as_view()
