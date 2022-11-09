from operator import itemgetter

import pandas as pd
from bokeh.embed import components
from bokeh.models import DatetimeTickFormatter, HoverTool, NumeralTickFormatter
from bokeh.plotting import figure
from django.db.models import F, Sum, Window
from django.shortcuts import render

from .filters import CurrentTotalFilter, MonthlyTimelineFilter, RankingsFilter
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
                expression=Sum(F("pv_net_nominal_capacity")),
                order_by=[
                    "date",
                ],
            ),
            wind_net_sum=Window(
                expression=Sum(F("wind_net_nominal_capacity")),
                order_by=[
                    "date",
                ],
            ),
            biomass_net_sum=Window(
                expression=Sum(F("biomass_net_nominal_capacity")),
                order_by=[
                    "date",
                ],
            ),
            hydro_net_sum=Window(
                expression=Sum(F("hydro_net_nominal_capacity")),
                order_by=[
                    "date",
                ],
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
    total_net_nominal_capacity = []

    # loop over each admin scope
    for i in order[order.index(realm_type) : :]:  # noqa: E203
        total_net_nominal_capacity.append(
            (
                current_object.get_scope_name(i),
                current_object.scope_average(i)[i],
                current_object.ratio_and_rank(
                    "total_net_nominal_capacity", "population", realm_type, i
                ),
            )
        )
        # max is needed to calculate width of the css progress bar
        print(total_net_nominal_capacity)
        get_max = max(total_net_nominal_capacity, key=itemgetter(1))[1]

    return render(
        request,
        "mastr_data/totals.html",
        {
            "script": script,
            "div": div,
            "filter": f_current_totals,
            "total_net_nominal_capacity": total_net_nominal_capacity,
            "div_timeline": div_timeline,
            "get_max": get_max,
        },
    )


def rankings_view(request):
    tempdict = request.GET
    county = tempdict.get("county")
    state = tempdict.get("state")

    f = RankingsFilter(tempdict, queryset=CurrentTotal.objects.all())

    if county:
        realm_type = "county"
        values_type = "municipality"
    elif state:
        realm_type = "state"
        values_type = "county"
    else:
        realm_type = "country"
        values_type = "state"

    filter_dict = {
        "county": {"county": county},
        "state": {"state": state},
        "country": {},
    }

    ranking = (
        CurrentTotal.objects.filter(**filter_dict.get(realm_type))
        .exclude(nnc_per_capita__isnull=True)
        .values_list(values_type)
        .annotate(numerator=Sum("population"))
        .annotate(denominator=Sum("total_net_nominal_capacity"))
        .annotate(score=Sum("total_net_nominal_capacity") / Sum("population"))
        .order_by("-score")
    )

    return render(
        request,
        "mastr_data/rankings.html",
        {"filter": f, "rankings": ranking},
    )
