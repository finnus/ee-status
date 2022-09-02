import django_filters
from django.db.models import Q, Sum

from ee_status.energy_sources.models import CurrentTotal, MonthlyTimeline

STATES = (
    ("Baden-Württemberg", "Baden-Württemberg"),
    ("Bayern", "Bayern"),
    ("Berlin", "Berlin"),
    ("Brandenburg", "Brandenburg"),
    ("Bremen", "Bremen"),
    ("Hamburg", "Hamburg"),
    ("Hessen", "Hessen"),
    ("Mecklenburg-Vorpommern", "Mecklenburg-Vorpommern"),
    ("Niedersachsen", "Niedersachsen"),
    ("Nordrhein-Westfalen", "Nordrhein-Westfalen"),
    ("Rheinland-Pfalz", "Rheinland-Pfalz"),
    ("Saarland", "Saarland"),
    ("Sachsen", "Sachsen"),
    ("Sachsen-Anhalt", "Sachsen-Anhalt"),
    ("Schleswig-Holstein", "Schleswig-Holstein"),
    ("Thüringen", "Thüringen"),
    ("Ausschließliche Wirtschaftszone", "Ausschließliche Wirtschaftszone"),
)
ENERGY_SOURCES = (
    ("Solare Strahlungsenergie", "Solare Strahlungsenergie"),
    ("Wasser", "Wasser"),
    ("Biomasse", "Biomasse"),
    ("Wind", "Wind"),
)


class MonthlyTimelineFilter(django_filters.FilterSet):
    energy_source = django_filters.ChoiceFilter(choices=ENERGY_SOURCES)
    state = django_filters.ChoiceFilter(choices=STATES)

    class Meta:
        model = MonthlyTimeline
        fields = [
            "state",
            "energy_source",
            "zip_code",
            "commune",
            "county",
        ]


class CurrentTotalFilter(django_filters.FilterSet):
    state = django_filters.ChoiceFilter(choices=STATES)

    @property
    def sum(self):
        qs = super().qs

        return qs.aggregate(
            water_sum=Sum("net_nominal_capacity", filter=Q(energy_source="Wasser")),
            solar_sum=Sum(
                "net_nominal_capacity",
                filter=Q(energy_source="Solare Strahlungsenergie"),
            ),
            biomass_sum=Sum("net_nominal_capacity", filter=Q(energy_source="Biomasse")),
            wind_sum=Sum("net_nominal_capacity", filter=Q(energy_source="Wind")),
        )

    class Meta:
        model = CurrentTotal
        fields = [
            "state",
            "zip_code",
            "commune",
            "county",
        ]
