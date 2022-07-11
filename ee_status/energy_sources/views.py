from django.db.models import F, Sum, Window
from django_filters.views import FilterView

from .filters import EnergySourcesFilter
from .models import EnergySources


class EnergySourcesListView(FilterView):
    context_object_name = "energy_sources_list"
    filterset_class = EnergySourcesFilter

    queryset = (
        EnergySources.objects.exclude(inbetriebnahmedatum__isnull=True)
        .filter(einheitbetriebsstatus="In Betrieb")
        .annotate(
            net_sum=Window(
                expression=Sum(F("nettonennleistung")),
                order_by=("inbetriebnahmedatum", "einheitmastrnummer"),
            )
        )
    )

    template_name = "energy_sources/solar_extended_list.html"


energy_sources_list_view = EnergySourcesListView.as_view()
