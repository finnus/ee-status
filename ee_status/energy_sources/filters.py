import django_filters

from ee_status.energy_sources.models import SolarExtended


class SolarExtendedFilter(django_filters.FilterSet):
    BUNDESLAENDER = (
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
    )
    bundesland = django_filters.ChoiceFilter(choices=BUNDESLAENDER)

    class Meta:
        model = SolarExtended
        fields = ["postleitzahl", "bundesland", "landkreis"]
