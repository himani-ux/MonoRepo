from __future__ import annotations

from types import SimpleNamespace
import unittest

from tests.safety.support import bootstrap_django, recreate_soi_tables


bootstrap_django(root_urlconf="apps.safety.urls")

from django.db import connection
from rest_framework.test import APIRequestFactory, force_authenticate

from apps.safety.views.soi_compliance import SOIComplianceView


def build_user():
    return SimpleNamespace(
        id="dpa-1",
        username="dpa-1",
        role_name="DPA",
        form_ids=["SAF_F_004"],
        process_ids=[],
        vessel_ids=["7"],
        is_global=False,
    )


class SOIComplianceLabelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        bootstrap_django(root_urlconf="apps.safety.urls")

    def setUp(self) -> None:
        recreate_soi_tables()
        self.factory = APIRequestFactory()
        self.view = SOIComplianceView.as_view()
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO master_soi_area (
                    area_id,
                    area_name,
                    section_12_flag,
                    display_order,
                    active,
                    seeded_version
                ) VALUES (%s, %s, %s, %s, %s, %s)
                """,
                [3, "Navigating Bridge & Monkey Island", False, 3, True, "v1.0"],
            )

    def test_response_uses_literal_soi_compliance_percent_label(self) -> None:
        request = self.factory.get("/api/safety/soi/compliance/?vessel_id=7")
        force_authenticate(request, user=build_user())

        response = self.view(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["label"], "SOI Compliance %")
        self.assertNotEqual(response.data["label"], "Inspection Compliance %")
