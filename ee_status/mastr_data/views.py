import json

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from django.contrib.gis.db.models.functions import AsGeoJSON
from django.core.serializers import serialize
from django.db.models import F, Q, Sum, Window
from django.db.models.functions import Round
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.translation import gettext as _
from plotly.offline import plot

from .filters import CurrentTotalFilter, MonthlyTimelineFilter, RankingsFilter
from .models import CurrentTotal, MonthlyTimeline


def search_municipality(request):
    query = request.POST.get("search")
    # look up all municipalities that contain the text
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

    return render(
        request,
        "mastr_data/partials/search-results.html",
        {
            "municipality_results": municipality_results,
            "county_results": county_results,
            "state_results": state_results,
        },
    )


def multi_polygon_map(request):
    qs = (
        CurrentTotal.objects.filter(geom__isnull=False)
        .annotate(json=AsGeoJSON("geom", precision=4))
        .values("id", "json")
    )

    # Prepare the GeoJSON object
    json_object = json.loads(qs)

    return render(
        request,
        "mastr_data/map_template.html",
        {"geojson": json_object},
    )


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

    #  Build Graph
    # Extract data for each category (pv, wind, hydro, biomass)
    dates = [item[0] for item in data]
    pv_data = [item[1] if item[1] is not None else 0 for item in data]
    wind_data = [item[2] if item[2] is not None else 0 for item in data]
    hydro_data = [item[3] if item[3] is not None else 0 for item in data]
    biomass_data = [item[4] if item[4] is not None else 0 for item in data]

    # Create traces for each category
    trace_pv = go.Scatter(x=dates, y=pv_data, mode="lines", name=_("Photovoltaics"))
    trace_wind = go.Scatter(x=dates, y=wind_data, mode="lines", name=_("Wind power"))
    trace_hydro = go.Scatter(x=dates, y=hydro_data, mode="lines", name=_("Hydropower"))
    trace_biomass = go.Scatter(
        x=dates,
        y=biomass_data,
        mode="lines",
        name=_("Biomass"),
    )

    # Create the layout for the timeline graph
    layout = go.Layout(
        xaxis=dict(title=_("Date")),
        yaxis=dict(
            title=_("Power generation"),
        ),
        hovermode="x unified",
        template="plotly_white",
    )

    # Create a figure and add traces to it
    fig = go.Figure(
        data=[trace_pv, trace_wind, trace_hydro, trace_biomass], layout=layout
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

    if False:
        plot_qs = CurrentTotal.objects.filter(county__exact=county)

        geojson_data = serialize(
            "geojson",
            plot_qs,
            geometry_field="geom",
            fields=["pk"],
        )
        if denominator:
            data = plot_qs.values("pk", "municipality", numerator, denominator)
            df = pd.DataFrame.from_records(data)
            df[numerator] = (df[numerator] / df[denominator]).astype(float).round(2)
        else:
            data = plot_qs.values("pk", "municipality", numerator)
            df = pd.DataFrame.from_records(data)
            df[numerator] = df[numerator].astype(float).round(2)

        geojson = json.loads(geojson_data)

        first_feature = geojson["features"][0]
        coordinates = first_feature["geometry"]["coordinates"]

        fig = px.choropleth_mapbox(
            df,
            geojson=geojson,
            locations="pk",
            color=numerator,
            featureidkey="properties.pk",
            color_continuous_scale="greens",
            center={"lat": coordinates[0][0][0][1], "lon": coordinates[0][0][0][0]},
            zoom=8,
            opacity=0.5,
            labels={},
            custom_data=["municipality"],
            mapbox_style="carto-positron",
        )

        fig.update_traces(
            hovertemplate="<b>%{customdata[0]}</b><br> %{z}",
        )
        fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})
        fig.update_layout(
            coloraxis_colorbar=dict(
                title="",  # Customize the legend title
                x=0,  # Adjust the x position of the color legend
                xanchor="left",  # Anchor the legend to the left side
            ),
        )
        plt_div = plot(fig, output_type="div", include_plotlyjs=False)
    else:
        plt_div = ""
    return render(
        request,
        "mastr_data/rankings.html",
        {
            "filter": f,
            "rankings": ranking,
            "table_captions": table_captions,
            "hierarchy": hierarchy,
            "basics": basics,
            "plt_div": plt_div,
        },
    )


def search_view(request):
    return render(request, "mastr_data/search.html")
