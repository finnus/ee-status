import django_filters

from ee_status.energy_sources.models import MonthlyTimeline


class MonthlyTimelineFilter(django_filters.FilterSet):
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
    state = django_filters.ChoiceFilter(choices=STATES)
    ENERGY_SOURCES = (
        ("Solare Strahlungsenergie", "Solare Strahlungsenergie"),
        ("Wasser", "Wasser"),
        ("Biomasse", "Biomasse"),
        ("Wind", "Wind"),
    )
    energy_source = django_filters.ChoiceFilter(choices=ENERGY_SOURCES)

    class Meta:
        model = MonthlyTimeline
        fields = ["state", "energy_source", "zip_code", "commune", "county"]
