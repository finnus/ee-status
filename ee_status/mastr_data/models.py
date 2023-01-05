from operator import itemgetter

from django.db import models
from django.db.models import Sum
from django.utils.translation import gettext_lazy as _


class EnergyUnit(models.Model):
    unit_nr = models.CharField(verbose_name=_("Unit Nr."), max_length=200)
    municipality_key = models.CharField(
        verbose_name=_("Municipality Key"), max_length=200
    )
    municipality = models.CharField(verbose_name=_("Municipality"), max_length=200)
    county = models.CharField(verbose_name=_("County"), max_length=200)
    state = models.CharField(verbose_name=_("State"), max_length=200, blank=True)
    zip_code = models.CharField(verbose_name=_("Zip-Code"), max_length=7, blank=True)
    start_up_date = models.DateTimeField(verbose_name=_("Start Up Date"), default=None)
    close_down_date = models.DateTimeField(
        verbose_name=_("Close Down Date"), default=None
    )
    date = models.DateTimeField(verbose_name=_("Corrected Date"), default=None)
    pv_net_nominal_capacity = models.FloatField(
        verbose_name=_("PV net nominal capacity")
    )
    wind_net_nominal_capacity = models.FloatField(
        verbose_name=_("Wind net nominal capacity")
    )
    biomass_net_nominal_capacity = models.FloatField(
        verbose_name=_("Biomass net nominal capacity")
    )
    hydro_net_nominal_capacity = models.FloatField(
        verbose_name=_("Hydro net nominal capacity")
    )
    storage_net_nominal_capacity = models.FloatField(
        verbose_name=_("Storage net nominal capacity")
    )

    class Meta:
        managed = False
        db_table = "energy_units"


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
        verbose_name=_("Municipality Key"), max_length=200
    )
    municipality = models.CharField(verbose_name=_("Municipality"), max_length=200)
    county = models.CharField(verbose_name=_("County"), max_length=200)
    state = models.CharField(verbose_name=_("State"), max_length=200, blank=True)
    zip_code = models.CharField(verbose_name=_("Zip-Code"), max_length=500, blank=True)
    pv_net_nominal_capacity = models.FloatField(
        verbose_name=_("PV net nominal capacity")
    )
    wind_net_nominal_capacity = models.FloatField(
        verbose_name=_("Wind net nominal capacity")
    )
    biomass_net_nominal_capacity = models.FloatField(
        verbose_name=_("Biomass net nominal capacity")
    )
    hydro_net_nominal_capacity = models.FloatField(
        verbose_name=_("Hydro net nominal capacity")
    )
    storage_net_nominal_capacity = models.FloatField(
        verbose_name=_("Storage net nominal capacity")
    )
    total_net_nominal_capacity = models.FloatField(
        verbose_name=_("total net nominal capacity")
    )
    population = models.IntegerField(verbose_name=_("Population"))
    area = models.FloatField(verbose_name="Area")

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
            "{}__{}".format(denominator, "isnull"): False,
            "{}__{}".format(denominator, "gt"): 0,
        }

        if realm_type == "country":
            realm_type_for_values = "state"
        else:
            realm_type_for_values = realm_type

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
            rank = str(
                [i for i, d in enumerate(ranking) if self_dict.get(realm_type) in d][0]
                + 1
            )

        ranking_without_none = [t for t in ranking if None not in t]
        max_value = round(max(ranking_without_none, key=itemgetter(1))[1], 1)

        return rank, len(ranking), max_value

    def scope_average(self, numerator, denominator, scope):
        scope_dict = {
            "municipality": {"municipality": self.municipality},
            "county": {"county": self.county},
            "state": {"state": self.state},
            "country": {},
        }

        scope_average = CurrentTotal.objects.filter(**scope_dict.get(scope)).aggregate(
            **{scope: Sum(numerator) / Sum(denominator)}
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
        for i in order[order.index(realm_type) : :]:  # noqa: E203
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
