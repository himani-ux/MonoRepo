from django.apps import AppConfig


class InspectionConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.inspection'
    verbose_name = 'PSC Inspection'

    def ready(self):
        """Register signals when app is ready."""
        # Import signals to register them
        from . import signals  # noqa: F401
