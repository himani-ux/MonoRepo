from __future__ import annotations

from types import SimpleNamespace
import unittest

from tests.safety.support import (
    bootstrap_django,
    recreate_phase5_reference_tables,
    recreate_soi_tables,
    recreate_taxonomy_reference_tables,
    seed_phase5_reference_tables,
)


bootstrap_django(root_urlconf="config.urls")

from django.db import connection
from rest_framework.test import APIRequestFactory, force_authenticate

from apps.safety.models import SafetyFieldHistory, SafetyCaseStudy
from apps.safety.views.taxonomy_admin import (
    CaseStudyHelpDrawerListView,
    ReferenceCaseStudyListCreateView,
    ReferenceMscatDetailView,
    ReferenceMscatListView,
    ReferenceSOIItemDetailView,
    ReferenceSOIItemListView,
)


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


class TaxonomyAdminDpaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        bootstrap_django(root_urlconf="config.urls")

    def setUp(self) -> None:
        recreate_phase5_reference_tables()
        seed_phase5_reference_tables()
        recreate_soi_tables()
        recreate_taxonomy_reference_tables()
        self.factory = APIRequestFactory()

        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO master_immediate_causes (
                    id,
                    legacy_int_id,
                    category_id,
                    category_name,
                    subcode_id,
                    subcode_description,
                    cause_type
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                [
                    "00000000000000000000000000000001",
                    1,
                    1,
                    "Substandard Act",
                    "1.01",
                    "Failure to inspect workplace",
                    "IMMEDIATE_SUBSTANDARD_ACT",
                ],
            )
            cursor.execute(
                """
                INSERT INTO master_loss_types (
                    id,
                    legacy_int_id,
                    loss_type_id,
                    loss_type_name,
                    description
                ) VALUES (%s, %s, %s, %s, %s)
                """,
                ["00000000000000000000000000000002", 1, 1, "People", "Injury or health loss"],
            )
            cursor.execute(
                """
                INSERT INTO master_safety_incident_type (
                    id,
                    legacy_int_id,
                    type_code,
                    type_name,
                    imo_reportable,
                    description,
                    active
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                ["00000000000000000000000000000003", 1, "GROUNDING", "Grounding", True, "Grounding event", True],
            )
            cursor.execute(
                """
                INSERT INTO master_soi_area (
                    id,
                    legacy_int_id,
                    area_id,
                    area_name,
                    section_12_flag,
                    display_order,
                    active,
                    seeded_version
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                ["00000000000000000000000000000004", 1, 1, "External Deck Structure", False, 1, True, "v1.0"],
            )
            cursor.execute("DROP TABLE IF EXISTS master_soi_area_item")
            cursor.execute(
                """
                CREATE TABLE master_soi_area_item (
                    id CHAR(32) PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
                    legacy_int_id INTEGER UNIQUE,
                    area_id INTEGER NOT NULL,
                    area_name VARCHAR(128) NOT NULL,
                    subsection_id INTEGER NOT NULL,
                    subsection_name VARCHAR(128) NOT NULL,
                    item_number VARCHAR(16) NOT NULL,
                    description TEXT NOT NULL,
                    tier VARCHAR(16) NOT NULL,
                    active BOOLEAN NOT NULL DEFAULT 1,
                    seeded_version VARCHAR(16) NOT NULL DEFAULT 'v1.0',
                    schema_version INTEGER NOT NULL DEFAULT 1,
                    updated_by VARCHAR(128) NULL,
                    updated_date DATETIME NULL
                )
                """
            )
            cursor.execute(
                """
                INSERT INTO master_soi_area_item (
                    id,
                    legacy_int_id,
                    area_id,
                    area_name,
                    subsection_id,
                    subsection_name,
                    item_number,
                    description,
                    tier,
                    active,
                    seeded_version,
                    schema_version,
                    updated_by,
                    updated_date
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                [
                    "00000000000000000000000000000005",
                    1,
                    1,
                    "External Deck Structure",
                    1,
                    "External Deck Structure",
                    "1",
                    "Decks clean and non-slippery",
                    "BASELINE",
                    True,
                    "v1.0",
                    1,
                    None,
                    None,
                ],
            )
            cursor.executemany(
                """
                INSERT INTO master_safety_case_study (
                    id,
                    legacy_int_id,
                    slug,
                    title,
                    event_type,
                    loss_summary,
                    incident_date,
                    immediate_cause_codes,
                    basic_cause_codes,
                    narrative,
                    recommendations,
                    source_label,
                    active,
                    display_order,
                    created_by
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                [
                    (
                        "00000000000000000000000000000006",
                        1,
                        "navigator",
                        "Navigator",
                        "Type 14 Grounding",
                        "Asset and reputation loss",
                        "2013-09-18",
                        "5, 10x2, 16, 17, 39",
                        "5, 8, 12",
                        "Navigator grounding narrative.",
                        "Navigator recommendations.",
                        "DNV worked solution",
                        True,
                        1,
                        "seed_case_studies",
                    ),
                    (
                        "00000000000000000000000000000007",
                        2,
                        "sinkfast",
                        "Sinkfast",
                        "Type 16/17 Fire and Explosion",
                        "People, asset, and environmental loss",
                        "2015-09-19",
                        "2, 4, 8, 17, 25, 33",
                        "4.9, 5, 9, 12.7, 16",
                        "Sinkfast explosion narrative.",
                        "Sinkfast recommendations.",
                        "DNV worked solution",
                        True,
                        2,
                        "seed_case_studies",
                    ),
                ],
            )

    def test_non_dpa_cannot_read_reference_admin_surface(self) -> None:
        request = self.factory.get("/api/safety/reference/mscat/")
        force_authenticate(
            request,
            user=build_user(role_name="FM", form_ids=["SAF_F_018"], process_ids=[]),
        )

        response = ReferenceMscatListView.as_view()(request)

        self.assertEqual(response.status_code, 403)

    def test_dpa_can_patch_mscat_and_audit_row_is_recorded(self) -> None:
        request = self.factory.patch(
            "/api/safety/reference/mscat/10.15/",
            {"subcode_description": "Independent review absent before route change."},
            format="json",
        )
        force_authenticate(
            request,
            user=build_user(role_name="DPA", form_ids=["SAF_F_018"], process_ids=["SAF_P_018"]),
        )

        response = ReferenceMscatDetailView.as_view()(request, subcode_id="10.15")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["subcode_id"], "10.15")
        self.assertEqual(
            response.data["subcode_description"],
            "Independent review absent before route change.",
        )
        self.assertTrue(
            SafetyFieldHistory.objects.filter(
                parent_table="master_mscat_taxonomy",
                field_name="subcode_description",
                change_reason="DPA updated M-SCAT taxonomy.",
            ).exists()
        )

    def test_dpa_can_patch_soi_item_with_soi_taxonomy_process(self) -> None:
        request = self.factory.patch(
            "/api/safety/reference/soi-items/1/",
            {"description": "Deck surfaces remain clean, clear, and non-slippery."},
            format="json",
        )
        force_authenticate(
            request,
            user=build_user(role_name="DPA", form_ids=["SAF_F_018"], process_ids=["SAF_P_019"]),
        )

        response = ReferenceSOIItemDetailView.as_view()(request, pk=1)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data["description"],
            "Deck surfaces remain clean, clear, and non-slippery.",
        )
        self.assertTrue(
            SafetyFieldHistory.objects.filter(
                parent_table="master_soi_area_item",
                field_name="description",
                change_reason="DPA updated SOI checklist item.",
            ).exists()
        )

    def test_soi_item_reference_list_uses_numeric_item_order(self) -> None:
        with connection.cursor() as cursor:
            cursor.executemany(
                """
                INSERT INTO master_soi_area_item (
                    id,
                    legacy_int_id,
                    area_id,
                    area_name,
                    subsection_id,
                    subsection_name,
                    item_number,
                    description,
                    tier,
                    active,
                    seeded_version,
                    schema_version
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                [
                    (
                        "00000000000000000000000000000008",
                        2,
                        1,
                        "External Deck Structure",
                        1,
                        "External Deck Structure",
                        "10",
                        "Tenth checklist item",
                        "BASELINE",
                        True,
                        "v1.0",
                        1,
                    ),
                    (
                        "00000000000000000000000000000009",
                        3,
                        1,
                        "External Deck Structure",
                        1,
                        "External Deck Structure",
                        "2",
                        "Second checklist item",
                        "BASELINE",
                        True,
                        "v1.0",
                        1,
                    ),
                ],
            )
        request = self.factory.get("/api/safety/reference/soi-items/?area_id=1")
        force_authenticate(
            request,
            user=build_user(role_name="CO", form_ids=["SAF_F_004"], process_ids=[]),
        )

        response = ReferenceSOIItemListView.as_view()(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual([row["item_number"] for row in response.data], ["1", "2", "10"])

    def test_incident_form_user_can_read_case_study_help_drawer_seed(self) -> None:
        request = self.factory.get("/api/safety/master/case-studies/")
        force_authenticate(
            request,
            user=build_user(role_name="MASTER", form_ids=["SAF_F_001"], process_ids=[]),
        )

        response = CaseStudyHelpDrawerListView.as_view()(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual([row["slug"] for row in response.data], ["navigator", "sinkfast"])

    def test_dpa_can_create_case_study_in_reference_admin_surface(self) -> None:
        request = self.factory.post(
            "/api/safety/reference/case-studies/",
            {
                "slug": "bridgewatch",
                "title": "Bridgewatch",
                "event_type": "Type 10 Navigation",
                "loss_summary": "Process and asset risk near grounding.",
                "incident_date": "2026-04-30",
                "immediate_cause_codes": "10, 17",
                "basic_cause_codes": "5, 8",
                "narrative": "Worked example for route monitoring drift.",
                "recommendations": "Refresh passage planning, verify ECDIS settings, and brief watch handover discipline.",
                "source_label": "Safety admin",
                "active": True,
                "display_order": 3,
            },
            format="json",
        )
        force_authenticate(
            request,
            user=build_user(role_name="DPA", form_ids=["SAF_F_018"], process_ids=["SAF_P_018"]),
        )

        response = ReferenceCaseStudyListCreateView.as_view()(request)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["slug"], "bridgewatch")
        self.assertTrue(SafetyCaseStudy.objects.filter(slug="bridgewatch").exists())
        self.assertTrue(
            SafetyFieldHistory.objects.filter(
                parent_table="master_safety_case_study",
                field_name="title",
                change_reason="DPA created Safety case study.",
            ).exists()
        )
