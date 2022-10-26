from django.db import models
from django.db.models import Sum


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
    municipality_key = models.CharField(max_length=200)
    municipality = models.CharField(max_length=200)
    county = models.CharField(max_length=200)
    state = models.CharField(max_length=200, blank=True)
    pv_net_nominal_capacity = models.FloatField()
    wind_net_nominal_capacity = models.FloatField()
    biomass_net_nominal_capacity = models.FloatField()
    hydro_net_nominal_capacity = models.FloatField()
    total_net_nominal_capacity = models.FloatField()
    population = models.IntegerField()
    nnc_per_capita = models.FloatField()

    class Meta:
        managed = False
        db_table = "current_totals"

    def nnc_per_capita_rank_within_county(self):
        county = self.county
        municipalities_ranking = (
            CurrentTotal.objects.filter(county=county)
            .exclude(nnc_per_capita__isnull=True)
            .values("municipality_key")
            .annotate(score=Sum("total_net_nominal_capacity") / Sum("population"))
            .order_by("-score")
        )
        nnc_per_capita_rank_within_county = [
            i
            for i, d in enumerate(municipalities_ranking)
            if self.municipality_key in d.values()
        ]

        return nnc_per_capita_rank_within_county

    def nnc_per_capita_rank_within_state(self, scope):
        if scope == "county":
            me = self.county
        elif scope == "municipality_key":
            me = self.municipality_key

        state = self.state
        ranking = (
            CurrentTotal.objects.filter(state=state)
            .exclude(nnc_per_capita__isnull=True)
            .values(scope)
            .annotate(score=Sum("total_net_nominal_capacity") / Sum("population"))
            .order_by("-score")
        )
        nnc_per_capita_rank_within_state_general = [
            i for i, d in enumerate(ranking) if me in d.values()
        ]

        return nnc_per_capita_rank_within_state_general

    def nnc_per_capita_rank_within_germany(self, scope):
        if scope == "county":
            me = self.county
        elif scope == "municipality_key":
            me = self.municipality_key
        elif scope == "state":
            me = self.state

        national_ranking = (
            CurrentTotal.objects.all()
            .exclude(nnc_per_capita__isnull=True)
            .values(scope)
            .annotate(score=Sum("total_net_nominal_capacity") / Sum("population"))
            .order_by("-score")
        )
        nnc_per_capita_rank_within_germany = [
            i for i, d in enumerate(national_ranking) if me in d.values()
        ]

        return nnc_per_capita_rank_within_germany
