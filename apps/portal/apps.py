from django.apps import AppConfig


class PortalConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.portal'
    verbose_name = 'Portail'

    def ready(self):
        import apps.portal.signals
