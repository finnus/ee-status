import pandas as pd
from bokeh.embed import components
from bokeh.models import DatetimeTickFormatter, HoverTool, NumeralTickFormatter
from bokeh.plotting import figure
from django.db.models import F, Sum, Window
from django.shortcuts import render

from .filters import CurrentTotalFilter, MonthlyTimelineFilter
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
    f_current_totals = CurrentTotalFilter(
        request.GET, queryset=CurrentTotal.objects.all()
    )
    # get the queryset to depict data for the graphs
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

    # aggregate the results as we want to display sums and not lists of objects
    totals = f_current_totals.qs.aggregate(
        pv_net_sum=Sum("pv_net_nominal_capacity"),
        wind_net_sum=Sum("wind_net_nominal_capacity"),
        biomass_net_sum=Sum("biomass_net_nominal_capacity"),
        hydro_net_sum=Sum("hydro_net_nominal_capacity"),
        nnc_per_capita=Sum("total_net_nominal_capacity") / Sum("population"),
    )

    # draw the plots with bokeh
    net_nominal_capacity_plot = figure(plot_width=400, plot_height=400)
    net_nominal_capacity_plot.hbar(
        y=[1, 2, 3, 4, 5],
        right=list(totals.values()),
        height=0.5,
    )

    # get the ranks
    nnc_per_capita_rank_within_county = "n.a."
    nnc_per_capita_rank_within_state = "n.a."
    nnc_per_capita_rank_within_germany = "n.a."
    if municipality or municipality_key:
        if municipality_key:
            municipality_object = CurrentTotal.objects.get(
                municipality_key=municipality_key
            )
        else:
            municipality_object = CurrentTotal.objects.get(municipality=municipality)

        nnc_per_capita_rank_within_county = (
            municipality_object.nnc_per_capita_rank_within_county()
        )
        nnc_per_capita_rank_within_state = (
            municipality_object.nnc_per_capita_rank_within_state("municipality_key")
        )
        nnc_per_capita_rank_within_germany = (
            municipality_object.nnc_per_capita_rank_within_germany("municipality_key")
        )

    elif county:
        county_object = CurrentTotal.objects.filter(county=county).first()
        nnc_per_capita_rank_within_state = (
            county_object.nnc_per_capita_rank_within_state("county")
        )
        nnc_per_capita_rank_within_germany = (
            county_object.nnc_per_capita_rank_within_germany("county")
        )

    elif state:
        state_object = CurrentTotal.objects.filter(state=state).first()
        nnc_per_capita_rank_within_germany = (
            state_object.nnc_per_capita_rank_within_germany("state")
        )

    ranks = {
        "nnc_per_capita_rank_within_county": nnc_per_capita_rank_within_county,
        "nnc_per_capita_rank_within_state": nnc_per_capita_rank_within_state,
        "nnc_per_capita_rank_within_germany": nnc_per_capita_rank_within_germany,
    }

    script, div = components((p, net_nominal_capacity_plot))
    return render(
        request,
        "mastr_data/totals.html",
        {
            "script": script,
            "div": div,
            "data": data,
            "filter": f,
            "ranks": ranks,
            "totals": totals,
        },
    )
