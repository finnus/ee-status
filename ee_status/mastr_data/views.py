import pandas as pd
from bokeh.embed import components
from bokeh.models import DatetimeTickFormatter, NumeralTickFormatter
from bokeh.plotting import figure
from django.db.models import F, Q, Sum, Window
from django.shortcuts import render

from .filters import CurrentTotalFilter, MonthlyTimelineFilter
from .models import CurrentTotal, MonthlyTimeline


def monthly_timeline_view(request):
    # get the filtered queryset from django-filters
    f = MonthlyTimelineFilter(request.GET, queryset=MonthlyTimeline.objects.all())

    # get the queryset to depict data for the graphs
    data = (
        f.qs.annotate(
            net_sum=Window(
                expression=Sum(F("net_nominal_capacity")),
                # partition_by=[F("energy_source")],
                order_by=[
                    "date",
                ],
            )
        )
        .distinct("date")
        .values_list("date", "net_sum")
    )

    # transform QuerySet to list
    data = list(data)
    # get only dates from list
    date_list = [e[0] for e in data]
    # transform dates to correct datetime
    date_list = pd.to_datetime(date_list)
    # get net_sums from list
    net_sum_list = [e[1] for e in data]
    TOOLTIPS = [
        ("date", "@date{%F}"),
        (
            "net_nominal_capacity",
            "$@{net_sum}{%0.2f}",
        ),  # use @{ } for field names with spaces
    ]
    p = figure(
        max_width=1200,
        plot_height=350,
        y_axis_type="datetime",
        y_axis_label="kWh",
        x_axis_label="year",
        sizing_mode="stretch_width",
        tooltips=TOOLTIPS,
    )
    p.line(date_list, net_sum_list, color="navy", alpha=0.5, line_width=2)
    p.yaxis[0].formatter = NumeralTickFormatter(format="0")
    p.xaxis[0].formatter = DatetimeTickFormatter(months="%m %Y")
    script, div = components(p)

    return render(
        request,
        "mastr_data/timeline.html",
        {
            "script": script,
            "div": div,
            "data": data,
            "filter": f,
        },
    )


def current_total_view(request):
    # get the filtered queryset from django-filters
    f = CurrentTotalFilter(request.GET, queryset=CurrentTotal.objects.all())

    # aggregate the results as we want to display sums and not lists of objects
    totals = f.qs.aggregate(
        water_sum=Sum("net_nominal_capacity", filter=Q(energy_source="Wasser")),
        solar_sum=Sum(
            "net_nominal_capacity",
            filter=Q(energy_source="Solare Strahlungsenergie"),
        ),
        biomass_sum=Sum("net_nominal_capacity", filter=Q(energy_source="Biomasse")),
        wind_sum=Sum("net_nominal_capacity", filter=Q(energy_source="Wind")),
    )

    # draw the plots with bokeh
    net_nominal_capacity_plot = figure(plot_width=400, plot_height=400)
    net_nominal_capacity_plot.hbar(
        y=[1, 2, 3, 4],
        right=list(totals.values()),
        height=0.5,
    )

    script, div = components(net_nominal_capacity_plot)
    return render(
        request,
        "mastr_data/current_total.html",
        {
            "script": script,
            "div": div,
            "totals": totals,
            "filter": f,
        },
    )
