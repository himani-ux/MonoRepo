from __future__ import annotations

import unittest

from django.urls import Resolver404, resolve

from tests.safety.support import bootstrap_django


bootstrap_django(root_urlconf="apps.safety.urls")


class SOINoScanUploadRouteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        bootstrap_django(root_urlconf="apps.safety.urls")

    def test_soi_upload_routes_are_not_registered(self) -> None:
        with self.assertRaises(Resolver404):
            resolve("/soi/42/upload/")

        with self.assertRaises(Resolver404):
            resolve("/soi/42/scan-upload/")

    def test_paper_first_routes_remain_registered(self) -> None:
        self.assertEqual(
            resolve("/soi/42/checklist/download/").url_name,
            "soi-checklist-download",
        )
        self.assertEqual(resolve("/soi/42/close/").url_name, "soi-close")
