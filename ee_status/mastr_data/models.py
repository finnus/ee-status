from django.db import models
from django.db.models import Sum
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
        db_table = "monthly_timeline_table"


class CurrentTotal(models.Model):
    municipality_key = models.CharField(
        verbose_name=_("Municipality Key"), max_length=200
    )
    municipality = models.CharField(verbose_name=_("Municipality"), max_length=200)
    county = models.CharField(verbose_name=_("County"), max_length=200)
    state = models.CharField(verbose_name=_("State"), max_length=200, blank=True)
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

    def ratio_and_rank(self, numerator, denominator, realm_type, scope):

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
            rank = [i for i, d in enumerate(ranking) if self_dict.get(realm_type) in d][
                0
            ] + 1

        return [(rank, len(ranking))]

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

        return scope_average

    def get_scope_name(self, scope):
        self_dict = {
            "municipality": self.municipality,
            "county": self.county,
            "state": self.state,
            "country": "Deutschland",
        }
        return self_dict.get(scope)
