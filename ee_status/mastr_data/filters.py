import django_filters

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
