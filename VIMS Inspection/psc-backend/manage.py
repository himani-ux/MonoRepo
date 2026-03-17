#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys


def _is_test_command(argv):
    return len(argv) > 1 and argv[1] == 'test'


def _has_explicit_settings(argv):
    for index, arg in enumerate(argv):
        if arg.startswith('--settings='):
            return True
        if arg == '--settings' and index + 1 < len(argv):
            return True
    return False


def main():
    """Run administrative tasks."""
    default_settings_module = 'core.settings'
    if _is_test_command(sys.argv) and not _has_explicit_settings(sys.argv):
        default_settings_module = 'core.settings_test'
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', default_settings_module)
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
