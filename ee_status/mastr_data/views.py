from operator import itemgetter

import pandas as pd
from bokeh.embed import components
from bokeh.models import DatetimeTickFormatter, HoverTool, NumeralTickFormatter
from bokeh.plotting import figure
from django.db.models import F, Sum, Window
from django.shortcuts import render
from django.utils.translation import gettext_lazy as _

from .filters import (
    CurrentTotalFilter,
    MonthlyTimelineFilter,
    RankingsFilter,
    SearchFilter,
)
from .models import CurrentTotal, MonthlyTimeline


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
            ],
            formatters={
                "@date_list": "datetime",  # use 'datetime' formatter for '@date' field
            },
            # display a tooltip whenever the cursor is vertically in line with a glyph
            mode="vline",
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

    # Determine which realm_type we are about to handle
    if municipality or municipality_key:
        realm_type = "municipality"
    elif county:
        realm_type = "county"
    elif state:
        realm_type = "state"
    else:
        realm_type = "country"

    # Define order for looping over multiple admin scopes
    order = ["municipality", "county", "state", "country"]

    # GET TOTAL NET NOMINAL CAPACITY PER CAPITA
    total_net_nominal_capacity_per_capita = []
    # loop over each administrative scope
    for i in order[order.index(realm_type) : :]:  # noqa: E203
        total_net_nominal_capacity_per_capita.append(
            (
                current_object.get_scope_name(i),
                current_object.scope_average(
                    "total_net_nominal_capacity", "population", i
                )[i],
                current_object.ratio_and_rank(
                    "total_net_nominal_capacity", "population", realm_type, i
                ),
            )
        )
        # max is needed to calculate width of the css progress bar
        total_net_nominal_capacity_per_capita_max = max(
            total_net_nominal_capacity_per_capita, key=itemgetter(1)
        )[1]

        # GET TOTAL NET NOMINAL CAPACITY PER SQUARE METERS
        total_net_nominal_capacity_per_sm = []
        # loop over each administrative scope
        for i in order[order.index(realm_type) : :]:  # noqa: E203
            total_net_nominal_capacity_per_sm.append(
                (
                    current_object.get_scope_name(i),
                    current_object.scope_average(
                        "total_net_nominal_capacity", "area", i
                    )[i],
                    current_object.ratio_and_rank(
                        "total_net_nominal_capacity", "area", realm_type, i
                    ),
                )
            )
            # max is needed to calculate width of the css progress bar
            total_net_nominal_capacity_per_sm_max = max(
                total_net_nominal_capacity_per_sm, key=itemgetter(1)
            )[1]

        # GET Storage Capacity per capita
        storage_capacity_per_capita = []
        # loop over each administrative scope
        for i in order[order.index(realm_type) : :]:  # noqa: E203
            storage_capacity_per_capita.append(
                (
                    current_object.get_scope_name(i),
                    current_object.scope_average(
                        "storage_net_nominal_capacity", "population", i
                    )[i],
                    current_object.ratio_and_rank(
                        "storage_net_nominal_capacity", "population", realm_type, i
                    ),
                )
            )
            # max is needed to calculate width of the css progress bar
            storage_capacity_per_capita_max = max(
                storage_capacity_per_capita, key=itemgetter(1)
            )[1]

    return render(
        request,
        "mastr_data/totals.html",
        {
            "script": script,
            "div": div,
            "filter": f_current_totals,
            "div_timeline": div_timeline,
            "total_net_nominal_capacity_per_capita": total_net_nominal_capacity_per_capita,
            "total_net_nominal_capacity_per_capita_max": total_net_nominal_capacity_per_capita_max,
            "total_net_nominal_capacity_per_sm": total_net_nominal_capacity_per_sm,
            "total_net_nominal_capacity_per_sm_max": total_net_nominal_capacity_per_sm_max,
            "storage_capacity_per_capita": storage_capacity_per_capita,
            "storage_capacity_per_capita_max": storage_capacity_per_capita_max,
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
            denominator_annotate = {"denominator": Sum(denominator)}
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
        .values_list(scope)
        .annotate(**numerator_annotate)
        .annotate(**denominator_annotate)
        .annotate(**score_expression)
        .order_by(*order_by_expression)
        .distinct()
    )

    return render(
        request,
        "mastr_data/rankings.html",
        {"filter": f, "rankings": ranking, "table_captions": table_captions},
    )


def search_view(request):
    result_list = CurrentTotal.objects.all()
    search_filter = SearchFilter(request.GET, queryset=result_list)
    return render(request, "mastr_data/search.html", {"filter": search_filter})
