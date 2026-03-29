from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class RecordsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.records'
    verbose_name = _('Medical Records')

    def ready(self):
        from . import signals  # noqa: F401
