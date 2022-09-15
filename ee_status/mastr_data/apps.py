from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class MastrDataConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "ee_status.mastr_data"
    verbose_name = _("MaStR Data")
