from django.apps import AppConfig


class CertsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.certs"
    label = "certs"
    verbose_name = "VIMS Certificates"
