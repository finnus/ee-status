from django.contrib import admin

from ee_status.mastr_data.models import CurrentTotal
from ee_status.mastr_data.models import MonthlyTimeline

admin.site.register(MonthlyTimeline)
admin.site.register(CurrentTotal)
