"""Pytest bootstrap for Django test runs without pytest-django plugin."""

import os

import django
from django.test.utils import (
    setup_databases,
    setup_test_environment,
    teardown_databases,
    teardown_test_environment,
)


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings_test')
django.setup()

_db_config = None


def pytest_sessionstart(session):
    """Create Django test DB once per pytest session."""
    global _db_config
    setup_test_environment()
    _db_config = setup_databases(verbosity=0, interactive=False)


def pytest_sessionfinish(session, exitstatus):
    """Tear down Django test DB/session test environment."""
    if _db_config is not None:
        teardown_databases(_db_config, verbosity=0)
    teardown_test_environment()
