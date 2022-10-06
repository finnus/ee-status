from django.db import models


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
    nnc_per_capita_rank_within_germany = models.IntegerField()
    nnc_per_capita_rank_within_state = models.IntegerField()
    nnc_per_capita_rank_within_county = models.IntegerField()

    class Meta:
        managed = False
        db_table = "current_totals"
