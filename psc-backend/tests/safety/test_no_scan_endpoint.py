from __future__ import annotations

import unittest

from django.urls import Resolver404, resolve

from tests.safety.support import bootstrap_django


bootstrap_django(root_urlconf="config.urls")


class NoScanEndpointTests(unittest.TestCase):
    def test_scan_upload_route_is_absent(self) -> None:
        with self.assertRaises(Resolver404):
            resolve("/api/safety/soi/42/scan/upload/")
