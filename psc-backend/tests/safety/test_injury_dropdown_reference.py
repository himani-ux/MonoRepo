from __future__ import annotations

from types import SimpleNamespace
import unittest

from tests.safety.support import bootstrap_django


bootstrap_django(root_urlconf="config.urls")

from django.db import connection
from rest_framework.test import APIRequestFactory, force_authenticate

from apps.safety.views.taxonomy_admin import ReferenceInjuryDropdownOptionListView


def build_user(*, role_name: str, form_ids: list[str], process_ids: list[str]) -> SimpleNamespace:
    return SimpleNamespace(
        id=f"{role_name.lower()}-1",
        username=f"{role_name.lower()}-1",
        role_name=role_name,
        form_ids=form_ids,
        process_ids=process_ids,
        vessel_ids=["7"],
        is_global=False,
    )


class InjuryDropdownReferenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        bootstrap_django(root_urlconf="config.urls")

    def setUp(self) -> None:
        with connection.cursor() as cursor:
            cursor.execute("DROP TABLE IF EXISTS vims_safety_injury_dropdown_option")
            cursor.execute(
                """
                CREATE TABLE vims_safety_injury_dropdown_option (
                    id CHAR(32) PRIMARY KEY,
                    field_key VARCHAR(32) NOT NULL,
                    option_label VARCHAR(255) NOT NULL,
                    display_order INTEGER NOT NULL,
                    active BOOLEAN NOT NULL DEFAULT 1,
                    created_by VARCHAR(128) NOT NULL DEFAULT 'system',
                    created_date DATETIME NULL,
                    updated_by VARCHAR(128) NULL,
                    updated_date DATETIME NULL
                )
                """
            )
            cursor.executemany(
                """
                INSERT INTO vims_safety_injury_dropdown_option (
                    id,
                    field_key,
                    option_label,
                    display_order,
                    active,
                    created_by
                ) VALUES (%s, %s, %s, %s, %s, %s)
                """,
                [
                    (
                        "00000000000000000000000000000011",
                        "TYPE_OF_ACTIVITY",
                        "Anchoring",
                        1,
                        True,
                        "migration",
                    ),
                    (
                        "00000000000000000000000000000012",
                        "TYPE_OF_ACTIVITY",
                        "Others(Specify)",
                        2,
                        True,
                        "migration",
                    ),
                    (
                        "00000000000000000000000000000013",
                        "NATURE_OF_INJURY",
                        "Cuts / Lacerations",
                        1,
                        True,
                        "migration",
                    ),
                ],
            )
        self.factory = APIRequestFactory()

    def test_reference_endpoint_filters_type_of_activity_options(self) -> None:
        request = self.factory.get("/api/safety/reference/injury-dropdown-options/?field_key=TYPE_OF_ACTIVITY")
        force_authenticate(
            request,
            user=build_user(role_name="MASTER", form_ids=["SAF_F_001"], process_ids=[]),
        )

        response = ReferenceInjuryDropdownOptionListView.as_view()(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual([row["option_label"] for row in response.data], ["Anchoring", "Others(Specify)"])
        self.assertEqual({row["field_key"] for row in response.data}, {"TYPE_OF_ACTIVITY"})
