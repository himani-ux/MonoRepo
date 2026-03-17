"""Django app configuration for CAR module."""

from django.apps import AppConfig


class CarConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.car'
    verbose_name = 'Corrective Action Reports'
