from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class EnergySourcesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "ee_status.energy_sources"
    verbose_name = _("Energy Sources")
