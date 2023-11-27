import django_filters
from django.utils.translation import gettext_lazy as _

from ee_status.mastr_data.models import CurrentTotal, MonthlyTimeline

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


class MonthlyTimelineFilter(django_filters.FilterSet):
    state = django_filters.ChoiceFilter(choices=STATES)

    class Meta:
        model = MonthlyTimeline
        fields = [
            "municipality_key",
            "municipality",
            "county",
            "state",
        ]


class CurrentTotalFilter(django_filters.FilterSet):
    state = django_filters.ChoiceFilter(choices=STATES)

    class Meta:
        model = CurrentTotal
        fields = [
            "municipality_key",
            "municipality",
            "county",
            "state",
        ]


class RankingsFilter(django_filters.FilterSet):
    VALUES = (
        ("total_net_nominal_capacity", _("Production Capacity (kW)")),
        ("storage_net_nominal_capacity", _("Storage Capacity (kWh)")),
        ("population", _("Population")),
        ("area", _("Area (km²)")),
    )
    SCOPES = (
        ("municipality", _("Municipalities")),
        ("county", _("Counties")),
        ("state", _("States")),
    )
    state = django_filters.ChoiceFilter(choices=STATES)
    scope = django_filters.ChoiceFilter(choices=SCOPES, label=_("Scope"))
    numerator = django_filters.ChoiceFilter(choices=VALUES, label=_("Rank by"))
    denominator = django_filters.ChoiceFilter(choices=VALUES, label=_("per"))

    class Meta:
        model = CurrentTotal
        fields = [
            "municipality",
            "county",
            "state",
            "scope",
            "numerator",
            "denominator",
        ]
