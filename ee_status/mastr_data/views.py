import pandas as pd
from bokeh.embed import components
from bokeh.models import DatetimeTickFormatter, HoverTool, NumeralTickFormatter
from bokeh.plotting import figure
from django.contrib import messages
from django.db.models import F, Q, Sum, Window
from django.db.models.functions import Coalesce, Round
from django.shortcuts import redirect, render, reverse
from django.utils.translation import gettext_lazy as _
from django_filters.views import FilterView

from .filters import (
    CurrentTotalFilter,
    EnergyUnitFilter,
    MonthlyTimelineFilter,
    RankingsFilter,
)
from .models import CurrentTotal, EnergyUnit, MonthlyTimeline


class EnergyUnitListView(FilterView):
    model = EnergyUnit
    context_object_name = "units_list"
    filterset_class = EnergyUnitFilter
    queryset = EnergyUnit.objects.order_by("-start_up_date").annotate(
        net_capacity=Coalesce(
            "pv_net_nominal_capacity",
            "wind_net_nominal_capacity",
            "hydro_net_nominal_capacity",
            "biomass_net_nominal_capacity",
            "storage_net_nominal_capacity",
        )
    )
    paginate_by = 50

    template_name = "mastr_data/energyunits_list.html"


energyunits_list_view = EnergyUnitListView.as_view()


def totals_view(request):
    tempdict = request.GET
    # some municipalities have the same name - currently, we just combine all municipalities with the same name
    # TODO: if multiple municipalities with same name but different municipality_keys, we first need the user to chose
    municipality_key = tempdict.get("municipality_key")
    municipality = tempdict.get("municipality")
    county = tempdict.get("county")
    state = tempdict.get("state")

    f = MonthlyTimelineFilter(tempdict, queryset=MonthlyTimeline.objects.all())
    data = (
        f.qs.annotate(
            pv_net_sum=Window(
                expression=Sum(F("pv_net_nominal_capacity")), order_by=("date",)
            ),
            wind_net_sum=Window(
                expression=Sum(F("wind_net_nominal_capacity")), order_by=("date",)
            ),
            biomass_net_sum=Window(
                expression=Sum(F("biomass_net_nominal_capacity")), order_by=("date",)
            ),
            hydro_net_sum=Window(
                expression=Sum(F("hydro_net_nominal_capacity")), order_by=("date",)
            ),
        )
        .distinct("date")
        .values_list(
            "date", "pv_net_sum", "wind_net_sum", "biomass_net_sum", "hydro_net_sum"
        )
    )

    # transform QuerySet to list
    data = list(data)
    # get only dates from list
    date_list = [e[0] for e in data]
    # transform dates to correct datetime
    date_list = pd.to_datetime(date_list)
    # get net_sums from list
    pv_net_sum_list = [e[1] for e in data]
    wind_net_sum_list = [e[2] for e in data]
    biomass_net_sum_list = [e[3] for e in data]
    hydro_net_sum_list = [e[4] for e in data]

    p = figure(
        max_width=1200,
        plot_height=350,
        y_axis_type="datetime",
        y_axis_label="kWh",
        x_axis_label="year",
        sizing_mode="stretch_width",
    )

    p.line(date_list, pv_net_sum_list, color="#F9A825", alpha=0.5, line_width=3)
    p.line(date_list, wind_net_sum_list, color="#424242", alpha=0.5, line_width=3)
    p.line(date_list, biomass_net_sum_list, color="#2E7D32", alpha=0.5, line_width=3)
    p.line(date_list, hydro_net_sum_list, color="#1565C0", alpha=0.5, line_width=3)
    p.yaxis[0].formatter = NumeralTickFormatter(format="0")
    p.xaxis[0].formatter = DatetimeTickFormatter(months="%m %Y")

    p.add_tools(
        HoverTool(
            tooltips=[
                ("date", "@date_list"),
                ("PV", "@pv_net_sum_list"),
                ("Wind", "@wind_net_sum_list"),
                ("Biomasse", "@biomass_net_sum_list"),
                ("Wasserkraft", "@hydro_net_sum_list"),
            ]
            # display a tooltip whenever the cursor is vertically in line with a glyph
        )
    )
    # define plots for bokeh
    plots = {
        "Timeline": p,
    }
    script, div = components(plots)
    div_timeline = div["Timeline"]

    f_current_totals = CurrentTotalFilter(
        request.GET, queryset=CurrentTotal.objects.all()
    )
    current_object = f_current_totals.qs.first()

    # Determine which realm type we are about to handle
    if municipality or municipality_key:
        realm_type = "municipality"
    elif county:
        realm_type = "county"
    elif state:
        realm_type = "state"
    else:
        realm_type = "country"

    # GET TOTAL NET NOMINAL CAPACITY PER CAPITA
    total_net_nominal_capacity_per_capita = current_object.ratio_and_rank(
        numerator="total_net_nominal_capacity",
        denominator="population",
        realm_type=realm_type,
    )
    print(total_net_nominal_capacity_per_capita)
    # GET TOTAL NET NOMINAL CAPACITY PER SQUARE METERS
    total_net_nominal_capacity_per_area = current_object.ratio_and_rank(
        numerator="total_net_nominal_capacity",
        denominator="area",
        realm_type=realm_type,
    )

    # GET Storage Capacity per capita
    storage_capacity_per_capita = current_object.ratio_and_rank(
        numerator="storage_net_nominal_capacity",
        denominator="population",
        realm_type=realm_type,
    )

    # GET Storage Capacity per are
    storage_capacity_per_area = current_object.ratio_and_rank(
        numerator="storage_net_nominal_capacity",
        denominator="area",
        realm_type=realm_type,
    )

    count_of_devices = CurrentTotalFilter(
        request.GET, queryset=EnergyUnit.objects.all()
    )
    count = count_of_devices.qs.filter(close_down_date__isnull=True).count()
    basics = f_current_totals.qs.aggregate(
        total_population=Sum("population"),
        total_area=Sum("area"),
        total_production_capacity=Sum("total_net_nominal_capacity"),
        total_storage_capacity=Sum("storage_net_nominal_capacity"),
        count_of_devices=Sum(count),
    )

    basics["realm_type"] = realm_type

    if realm_type == "country":
        basics["realm_name"] = _("Germany")
    else:
        basics["realm_name"] = getattr(current_object, realm_type)

    return render(
        request,
        "mastr_data/totals.html",
        {
            "script": script,
            "div": div,
            "filter": f_current_totals,
            "div_timeline": div_timeline,
            "total_net_nominal_capacity_per_capita": total_net_nominal_capacity_per_capita,
            "total_net_nominal_capacity_per_area": total_net_nominal_capacity_per_area,
            "storage_capacity_per_capita": storage_capacity_per_capita,
            "storage_capacity_per_area": storage_capacity_per_area,
            "basics": basics,
            "realm_type": realm_type,
        },
    )


def rankings_view(request):
    tempdict = request.GET
    county = tempdict.get("county")
    state = tempdict.get("state")
    scope = tempdict.get("scope")
    numerator = tempdict.get("numerator")
    denominator = tempdict.get("denominator")

    if not scope:
        scope = "state"
    if not numerator and not denominator:
        numerator = "total_net_nominal_capacity"
        denominator = "population"

    f = RankingsFilter(tempdict, queryset=CurrentTotal.objects.all())

    if county:
        realm_type = "county"
    elif state:
        realm_type = "state"
    else:
        realm_type = "country"

    filter_dict = {
        "county": {"county": county},
        "state": {"state": state},
        "country": {},
    }

    table_captions = [_("Rank"), scope]

    if numerator:
        numerator_annotate = {"numerator": Sum(numerator)}
        table_captions.append(CurrentTotal._meta.get_field(numerator).verbose_name)
        if denominator:
            denominator_filter_kwargs = {
                "{}__{}".format(denominator, "isnull"): False,
                "{}__{}".format(denominator, "gt"): 0,
            }
            denominator_annotate = {"denominator": Round(Sum(denominator))}
            score_expression = {"score": Sum(numerator) / Sum(denominator)}
            order_by_expression = ("-score",)
            table_captions.append(
                CurrentTotal._meta.get_field(denominator).verbose_name
            )
            table_captions.append(_("Score"))
        else:
            denominator_filter_kwargs = {}
            denominator_annotate = {}
            score_expression = {}
            order_by_expression = ("-numerator",)
    else:
        numerator_annotate = {}
        denominator_filter_kwargs = {}
        denominator_annotate = {}
        score_expression = {}
        order_by_expression = ()

    ranking = (
        CurrentTotal.objects.filter(**filter_dict.get(realm_type))
        .filter(**denominator_filter_kwargs)
        .values(scope)
        .annotate(**numerator_annotate)
        .annotate(**denominator_annotate)
        .annotate(**score_expression)
        .order_by(*order_by_expression)
        .distinct()
    )
    print(ranking)

    return render(
        request,
        "mastr_data/rankings.html",
        {"filter": f, "rankings": ranking, "table_captions": table_captions},
    )


def search_view(request):
    # if its get request, we get the search term via the "q" (specified in the form template)
    if request.method == "GET":
        query = request.GET.get("q")
        # if there is no search keyword, we return the search page again
        if not query:
            return render(request, "mastr_data/search.html")

    # Search logic
    # search for aliases of Germany
    # 0 results = nothing found
    # 1 result = single municipality or a municipality which is a county at the same time ("kreisfreie Stadt")
    # > 1 results:
    #   as many municipalities as the county counts -> county or municipality which contain the name of the county
    #   as many municipalities as the state -> state
    #   more results: return list of results for user

    names_for_germany = [
        "Germany",
        "Deutschland",
        "Bundesrepublik",
        "Schland",
        "alles",
        "BRD",
    ]
    if query in names_for_germany:
        return redirect(reverse("mastr_data:totals"))

    # we filter the CurrentTotal table by looking in all relevant columns
    qs_filtered = CurrentTotal.objects.filter(
        Q(municipality__icontains=query)
        | Q(county__icontains=query)
        | Q(state__icontains=query)
        | Q(municipality_key__icontains=query)
        | Q(zip_code__icontains=query)
    )

    # get the number of results
    number_of_results = len(qs_filtered)

    # No matches (no results found)
    if not qs_filtered:
        messages.add_message(
            request,
            messages.WARNING,
            _("We couldn't find anything. Try again with another keyword!"),
        )
        return render(request, "mastr_data/search.html")

    # if there is only one result, it's a single municipality or a county with only one municipality
    elif number_of_results == 1:
        # County with the same name and no other municipalities ("kreisfreie Stadt", e.g, "Freiburg im Breisgau")
        if qs_filtered[0].county == qs_filtered[0].municipality:
            # we return the county as the comparisons make more sense then
            return redirect(
                reverse("mastr_data:totals") + "?county=" + qs_filtered[0].county
            )
        # single municipality result
        else:
            return redirect(
                reverse("mastr_data:totals")
                + "?municipality="
                + qs_filtered[0].municipality
            )

    # if we have multiple results, it can be...
    elif number_of_results > 1:
        # we count the total numer of municipalities in the county
        municipalities_in_county = CurrentTotal.objects.filter(
            county=qs_filtered[0].county
        ).count()
        # we count the total numer of municpalities in the state
        municipalities_in_state = CurrentTotal.objects.filter(
            state=qs_filtered[0].state
        ).count()
        # if there are as many municipalities in the county as in the number of search results it probably the county
        if municipalities_in_county == number_of_results:
            # but there might be municipalities which include the name of the county (e.g. "Freising")
            # SEARCH RESULT IS A COUNTY AND ONE/MULTIPLE MUNICIPALITIES
            if CurrentTotal.objects.filter(municipality=qs_filtered[0].county).exists():
                result_list = qs_filtered.filter(
                    municipality__icontains=qs_filtered[0].county
                )
                # return the list of concerned municipalities and of the county itself (the user has to chose)
                return render(
                    request,
                    "mastr_data/search.html",
                    {
                        "municipality_results": result_list,
                        "county_results": qs_filtered[0],
                    },
                )
            # SEARCH RESULT IS A COUNTY
            else:
                return redirect(
                    reverse("mastr_data:totals") + "?county=" + qs_filtered[0].county
                )
        # SEARCH RESULT IS A FEDERAL STATE
        # if there are as many results as municipalities in the county it's the state itself
        elif municipalities_in_state == number_of_results:
            return redirect(
                reverse("mastr_data:totals") + "?state=" + qs_filtered[0].state
            )
        # if it's something undefined we return the results list of municipalites, counties and states
        else:

            return render(
                request, "mastr_data/search.html", {"municipality_results": qs_filtered}
            )

    return render(request, "mastr_data/search.html")
