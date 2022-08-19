from django.db import models


class MonthlyTimeline(models.Model):
    date = models.DateTimeField(default=None)
    net_nominal_capacity = models.FloatField()
    zip_code = models.CharField(max_length=200)
    commune = models.CharField(max_length=200)
    county = models.CharField(max_length=200)
    state = models.CharField(max_length=200, blank=True)
    energy_source = models.CharField(max_length=200)

    class Meta:
        managed = False
        db_table = "monthly_timeline"
