import pandas as pd
from bokeh.embed import components
from bokeh.models import DatetimeTickFormatter, HoverTool, NumeralTickFormatter
from bokeh.plotting import figure
from django.contrib import messages
from django.db.models import F, Q, Sum, Window
from django.shortcuts import redirect, render, reverse
from django.utils.translation import gettext_lazy as _

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

    # Determine which realm_type we are about to handle
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
        "total_net_nominal_capacity", "population", realm_type
    )
    # GET TOTAL NET NOMINAL CAPACITY PER SQUARE METERS
    total_net_nominal_capacity_per_sm = current_object.ratio_and_rank(
        "total_net_nominal_capacity", "area", realm_type
    )

    # GET Storage Capacity per capita
    storage_capacity_per_capita = current_object.ratio_and_rank(
        "storage_net_nominal_capacity", "population", realm_type
    )

    return render(
        request,
        "mastr_data/totals.html",
        {
            "script": script,
            "div": div,
            "filter": f_current_totals,
            "div_timeline": div_timeline,
            "total_net_nominal_capacity_per_capita": total_net_nominal_capacity_per_capita[
                0
            ],
            "total_net_nominal_capacity_per_capita_max": total_net_nominal_capacity_per_capita[
                1
            ],
            "total_net_nominal_capacity_per_sm": total_net_nominal_capacity_per_sm[0],
            "total_net_nominal_capacity_per_sm_max": total_net_nominal_capacity_per_sm[
                1
            ],
            "storage_capacity_per_capita": storage_capacity_per_capita[0],
            "storage_capacity_per_capita_max": storage_capacity_per_capita[1],
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
    if request.method == "GET":
        query = request.GET.get("q")
        if not query:
            return render(request, "mastr_data/search.html")

    qs_filtered = CurrentTotal.objects.filter(
        Q(municipality__icontains=query)
        | Q(county__icontains=query)
        | Q(state__icontains=query)
        | Q(municipality_key__icontains=query)
        | Q(zip_code__icontains=query)
    )

    # no results
    if not qs_filtered:
        messages.add_message(request, messages.INFO, "no result")
        return render(request, "mastr_data/search.html")

    # if there is only one result, it's a single municipality or a county with only one municipality
    elif len(qs_filtered) == 1:
        # County with the same name and no other municipalities.
        if qs_filtered[0].county == qs_filtered[0].municipality:
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
    elif len(qs_filtered) > 1:
        municipalities_in_county = CurrentTotal.objects.filter(
            county=qs_filtered[0].county
        ).count()
        municipalities_in_state = CurrentTotal.objects.filter(
            state=qs_filtered[0].state
        ).count()
        if municipalities_in_county == len(qs_filtered):
            # if there are less results than municiaplities in the county, the user has to chose what s/he meant
            if CurrentTotal.objects.filter(municipality=qs_filtered[0].county).exists():
                result_list = qs_filtered.filter(
                    municipality__icontains=qs_filtered[0].county
                )
                return render(
                    request,
                    "mastr_data/search.html",
                    {
                        "municipality_results": result_list,
                        "county_results": qs_filtered[0],
                    },
                )
            # or - if there are as many results as municipalities in the county it's probably the county itself
            else:
                return redirect(
                    reverse("mastr_data:totals") + "?county=" + qs_filtered[0].county
                )
        elif municipalities_in_state == len(qs_filtered):
            messages.add_message(request, messages.INFO, "a federal state")
            return redirect(
                reverse("mastr_data:totals") + "?state=" + qs_filtered[0].state
            )
        else:
            return render(
                request, "mastr_data/search.html", {"result_list": qs_filtered}
            )

    return render(request, "mastr_data/search.html")
