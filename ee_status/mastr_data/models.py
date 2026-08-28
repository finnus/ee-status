from operator import itemgetter

from django.db import models
from django.db.models import ExpressionWrapper
from django.db.models import FloatField
from django.db.models import Sum
from django.db.models.functions import NullIf
from django.utils.translation import gettext_lazy as _


class MonthlyTimeline(models.Model):
    date = models.DateTimeField(default=None)
    municipality_key = models.CharField(max_length=200)
    municipality = models.CharField(max_length=200)
    county = models.CharField(max_length=200)
    state = models.CharField(max_length=200, blank=True)
    pv_net_nominal_capacity = models.FloatField()
    wind_net_nominal_capacity = models.FloatField()
    biomass_net_nominal_capacity = models.FloatField()
    hydro_net_nominal_capacity = models.FloatField()

    class Meta:
        managed = False
        db_table = "monthly_timeline"


class CurrentTotal(models.Model):
    municipality_key = models.CharField(
        verbose_name=_("Municipality Key"),
        max_length=200,
    )
    municipality = models.CharField(verbose_name=_("Municipality"), max_length=200)
    county = models.CharField(verbose_name=_("County"), max_length=200)
    state = models.CharField(verbose_name=_("State"), max_length=200, blank=True)
    zip_code = models.CharField(verbose_name=_("Zip-Code"), max_length=500, blank=True)
    pv_net_nominal_capacity = models.FloatField(
        verbose_name=_("PV net nominal capacity (kW)"),
    )
    wind_net_nominal_capacity = models.FloatField(
        verbose_name=_("Wind net nominal capacity (kW)"),
    )
    biomass_net_nominal_capacity = models.FloatField(
        verbose_name=_("Biomass net nominal capacity (kW)"),
    )
    hydro_net_nominal_capacity = models.FloatField(
        verbose_name=_("Hydro net nominal capacity (kW)"),
    )
    storage_net_nominal_capacity = models.FloatField(
        verbose_name=_("Storage net nominal capacity (kWh)"),
    )
    total_net_nominal_capacity = models.FloatField(
        verbose_name=_("total net nominal capacity (kW)"),
    )
    population = models.IntegerField(verbose_name=_("Population"))
    area = models.FloatField(verbose_name=_("Area (km²)"))
    energy_units = models.IntegerField(verbose_name=_("Energy Units"))

    class Meta:
        managed = False
        db_table = "current_totals"

    def ratio_and_rank_per_scope(self, numerator, denominator, realm_type, scope):
        scope_dict = {
            "municipality": {"municipality": self.municipality},
            "county": {"county": self.county},
            "state": {"state": self.state},
            "country": {},
        }

        denominator_filter_kwargs = {
            f"{denominator}__isnull": False,
            f"{denominator}__gt": 0,
        }

        realm_type_for_values = "state" if realm_type == "country" else realm_type

        ranking = (
            CurrentTotal.objects.filter(**scope_dict.get(scope))
            .filter(**denominator_filter_kwargs)
            .values_list(realm_type_for_values)
            .annotate(score=Sum(numerator) / Sum(denominator))
            .order_by("-score")
        )
        self_dict = {
            "municipality": self.municipality,
            "county": self.county,
            "state": self.state,
        }

        if realm_type == scope:
            rank = "n.a"
        else:
            # The ranking only contains areas with a usable denominator, so the
            # area being displayed is absent from it whenever its own population
            # or area is zero or unknown. It then has no rank rather than rank 1.
            position = next(
                (i for i, d in enumerate(ranking) if self_dict.get(realm_type) in d),
                None,
            )
            rank = "n.a" if position is None else str(position + 1)

        ranking_without_none = [t for t in ranking if None not in t]
        max_value = (
            round(max(ranking_without_none, key=itemgetter(1))[1], 1)
            if ranking_without_none
            else 0
        )

        return rank, len(ranking), max_value

    def scope_average(self, numerator, denominator, scope):
        scope_dict = {
            "municipality": {"municipality": self.municipality},
            "county": {"county": self.county},
            "state": {"state": self.state},
            "country": {},
        }

        # NullIf keeps Postgres from raising "division by zero" for areas whose
        # population or area sums to zero, of which there are real examples
        # (Starnberger See, Sachsenwald). Those come back as None and read as 0.
        scope_average = CurrentTotal.objects.filter(**scope_dict.get(scope)).aggregate(
            **{
                scope: ExpressionWrapper(
                    Sum(numerator) / NullIf(Sum(denominator), 0),
                    output_field=FloatField(),
                ),
            },
        )
        return round(scope_average[scope] or 0, 2)

    def get_scope_name(self, scope):
        self_dict = {
            "municipality": self.municipality,
            "county": self.county,
            "state": self.state,
            "country": "Deutschland",
        }
        return self_dict.get(scope)

    def ratio_and_rank(self, numerator, denominator, realm_type):
        # Define order for looping over multiple admin scopes
        order = ["municipality", "county", "state", "country"]
        ratio_and_rank = []
        for i in order[order.index(realm_type) :]:
            new_scope_dict = {}
            new_scope_dict["realm_type"] = i
            new_scope_dict["realm_name"] = self.get_scope_name(i)
            new_scope_dict["score"] = self.scope_average(numerator, denominator, i)
            new_scope_dict["unit"] = "kW"
            new_scope_dict["numerator"] = numerator
            new_scope_dict["denominator"] = denominator
            rr = self.ratio_and_rank_per_scope(numerator, denominator, realm_type, i)
            new_scope_dict["rank"] = rr[0]
            new_scope_dict["total_ranks"] = rr[1]
            new_scope_dict["max_score"] = rr[2]
            ratio_and_rank.append(new_scope_dict)

        return ratio_and_rank
