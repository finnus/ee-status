import numpy as np
import pandas as pd
import plotly.express as px
from django.contrib import messages
from django.db.models import F, Q, Sum, Window
from django.db.models.functions import Round
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.translation import gettext as _
from plotly.offline import plot

from .filters import CurrentTotalFilter, MonthlyTimelineFilter, RankingsFilter
from .models import CurrentTotal, MonthlyTimeline


def totals_view(request):
    tempdict = request.GET
    municipality_key = tempdict.get("municipality_key")
    municipality = tempdict.get("municipality")
    county = tempdict.get("county")
    state = tempdict.get("state")

    f = MonthlyTimelineFilter(tempdict, queryset=MonthlyTimeline.objects.all())
    data = (
        f.qs.annotate(
            pv_net_sum=Window(
                expression=Sum(F("pv_net_nominal_capacity")), order_by=[F("date").asc()]
            ),
            wind_net_sum=Window(
                expression=Sum(F("wind_net_nominal_capacity")),
                order_by=[F("date").asc()],
            ),
            biomass_net_sum=Window(
                expression=Sum(F("biomass_net_nominal_capacity")),
                order_by=[F("date").asc()],
            ),
            hydro_net_sum=Window(
                expression=Sum(F("hydro_net_nominal_capacity")),
                order_by=[F("date").asc()],
            ),
        )
        .distinct("date")
        .values_list(
            "date", "pv_net_sum", "wind_net_sum", "biomass_net_sum", "hydro_net_sum"
        )
    )

    # transform QuerySet to list
    data = list(data)
    # transform to pandas DataFrame
    df = pd.DataFrame(
        data,
        columns=[
            "date",
            "pv_net_sum",
            "wind_net_sum",
            "biomass_net_sum",
            "hydro_net_sum",
        ],
    )
    # replace "None" by NaN
    df = df.fillna(value=np.nan)
    #  Build Graph
    fig = px.line(
        df,
        x="date",
        y=["pv_net_sum", "wind_net_sum", "biomass_net_sum", "hydro_net_sum"],
        hover_data={"date": "|%B %Y"},
        template="plotly_white",
        labels={"date": _("date"), "value": _("installed capacity (kW)")},
    )

    new = {
        "pv_net_sum": _("Photovoltaics"),
        "wind_net_sum": _("Wind power"),
        "biomass_net_sum": _("Biomass"),
        "hydro_net_sum": _("Hydropower"),
    }
    fig.for_each_trace(
        lambda t: t.update(
            name=new[t.name],
            legendgroup=new[t.name],
            hovertemplate=t.hovertemplate.replace(t.name, new[t.name]),
        )
    )

    fig.update_layout(
        legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01),
        legend_title_text=_("Power generation"),
    )
    plt_div = plot(fig, output_type="div", include_plotlyjs=False)

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

    basics = f_current_totals.qs.aggregate(
        total_population=Sum("population"),
        total_area=Sum("area"),
        total_production_capacity=Sum("total_net_nominal_capacity"),
        total_storage_capacity=Sum("storage_net_nominal_capacity"),
        count_of_devices=Sum("energy_units"),
    )
    basics["realm_type"] = realm_type

    if realm_type == "country":
        basics["realm_name"] = _("Germany")
    else:
        basics["realm_name"] = getattr(current_object, realm_type)

    order = ["municipality", "county", "state"]
    hierarchy = {}
    if realm_type != "country":
        for i in order[order.index(realm_type) : :]:  # noqa: E203
            hierarchy[i] = getattr(current_object, i)
    hierarchy["country"] = _("Germany")

    return render(
        request,
        "mastr_data/totals.html",
        {
            "filter": f_current_totals,
            "total_net_nominal_capacity_per_capita": total_net_nominal_capacity_per_capita,
            "total_net_nominal_capacity_per_area": total_net_nominal_capacity_per_area,
            "storage_capacity_per_capita": storage_capacity_per_capita,
            "storage_capacity_per_area": storage_capacity_per_area,
            "basics": basics,
            "hierarchy": hierarchy,
            "realm_type": realm_type,
            "plt_div": plt_div,
        },
    )


def rankings_view(request):
    tempdict = request.GET
    municipality = tempdict.get("municipality")
    county = tempdict.get("county")
    state = tempdict.get("state")
    numerator = tempdict.get("numerator")
    denominator = tempdict.get("denominator")
    scope = tempdict.get("scope")

    if not numerator and not denominator:
        numerator = "total_net_nominal_capacity"
        denominator = "population"

    f = RankingsFilter(tempdict, queryset=CurrentTotal.objects.all())

    if municipality:
        realm_type = "municipality"
    elif county:
        realm_type = "county"
    elif state:
        realm_type = "state"
    else:
        # when looking at germany, it should still display the different states
        realm_type = "state"

    hierarchy = {}

    if municipality:
        hierarchy["municipality"] = municipality
    if county:
        hierarchy["county"] = county
    if state:
        hierarchy["state"] = state

    hierarchy["country"] = _("Germany")

    basics = {"realm_type": realm_type, "realm_name": next(iter(hierarchy.values()))}

    table_captions = [_("Rank"), realm_type]

    if numerator:
        numerator_annotate = {"numerator": Sum(numerator)}
        table_captions.append(CurrentTotal._meta.get_field(numerator).verbose_name)
        numerator_filter_kwargs = {
            "{}__{}".format(numerator, "isnull"): False,
            "{}__{}".format(numerator, "gt"): 0,
        }
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
        numerator_filter_kwargs = {
            "{}__{}".format(numerator, "isnull"): False,
            "{}__{}".format(numerator, "gt"): 0,
        }

    filter_dict = {
        "municipality": {"municipality": municipality},
        "county": {"county": county},
        "state": {"state": state},
        "country": {},
    }

    if not scope:
        temp = list(filter_dict)
        try:
            scope = temp[temp.index(realm_type) + 1]
        except (ValueError, IndexError):
            scope = realm_type

    ranking = (
        CurrentTotal.objects.filter(**filter_dict.get(scope))
        .filter(**denominator_filter_kwargs)
        .filter(**numerator_filter_kwargs)
        .values(realm_type)
        .annotate(**numerator_annotate)
        .annotate(**denominator_annotate)
        .annotate(**score_expression)
        .order_by(*order_by_expression)
        .distinct()
    )

    return render(
        request,
        "mastr_data/rankings.html",
        {
            "filter": f,
            "rankings": ranking,
            "table_captions": table_captions,
            "hierarchy": hierarchy,
            "basics": basics,
        },
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

    municipality_results = (
        CurrentTotal.objects.filter(
            Q(municipality__icontains=query)
            | Q(municipality_key__icontains=query)
            | Q(zip_code__icontains=query)
        )
        # we exclude municipalities that are their own counties ("kreisfreie Städte")
        # their municipality keys ends with "000"
        .exclude(municipality_key__endswith="000").values(
            "municipality", "county", "state"
        )
    )

    county_results = (
        CurrentTotal.objects.filter(county__icontains=query)
        .values("county", "state")
        # we exclude counties that are their own states ("echte Stadtstaaten": Hamburg, Berlin)
        # their municipality keys ends with "000000"
        .exclude(municipality_key__endswith="000000")
        .distinct()
    )
    state_results = (
        CurrentTotal.objects.filter(state__icontains=query).values("state").distinct()
    )
    total_results = len(municipality_results) + len(county_results) + len(state_results)

    if total_results == 0:
        messages.add_message(
            request,
            messages.WARNING,
            _("We couldn't find anything. Try again with another keyword!"),
        )
        return render(request, "mastr_data/search.html")

    elif total_results == 1:
        if municipality_results:
            url_param = "?municipality=" + municipality_results[0]["municipality"]
        elif county_results:
            url_param = "?county=" + county_results[0]["county"]
        else:
            url_param = "?state=" + state_results[0]["state"]
        return redirect(reverse("mastr_data:totals") + url_param)
    else:
        return render(
            request,
            "mastr_data/search.html",
            {
                "municipality_results": municipality_results,
                "county_results": county_results,
                "state_results": state_results,
            },
        )

    return render(request, "mastr_data/search.html")
