from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch
import uuid
import os

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings_test")
django.setup()

from rest_framework import status
from rest_framework.test import APIRequestFactory, force_authenticate

from apps.accounts.backends import AuthenticatedUser
from apps.certs.services.catalog_repository import CatalogRepository, CatalogRowPage
from apps.certs.views.catalog_views import (
    CatalogRowAuditHistoryView,
    CatalogRowBulkSoftDeleteView,
    CatalogRowDeprecateView,
    CatalogRowDetailView,
    CatalogRowHardPurgeView,
    CatalogRowListCreateView,
    CatalogSectionListView,
)


def make_user(*, role: str, form_ids: list[str], process_ids: list[str]) -> AuthenticatedUser:
    return AuthenticatedUser(
        user_id=f"{role.lower().replace(' ', '-')}-1",
        user_type="OFFICE",
        full_name=f"{role} User",
        role=role,
        employee_id=f"{role[:3].upper()}001",
        form_ids=form_ids,
        process_ids=process_ids,
    )


def catalog_row(**overrides):
    row = {
        "catalog_id": uuid.uuid4(),
        "canonical_code": "STAT-IOPP",
        "section_id": 2,
        "section_code": "STATUTORY",
        "section_name": "Statutory & Flag",
        "display_name": "International Oil Pollution Prevention Certificate",
        "short_name": "IOPP",
        "print_section_label": "Statutory & Flag",
        "validity_type": "full",
        "cadence_months": 60,
        "cadence_custom_days": None,
        "issuing_authority_type": "flag",
        "is_class_tracked": False,
        "submission_scope": "master_only",
        "parent_id": None,
        "relationship_type_default": None,
        "applicable_ship_types": '["all"]',
        "mandatory_for_all_vessels": True,
        "applicability_mode": "all_matching_type",
        "specific_vessel_ids": None,
        "parent_supports_dynamic_children": False,
        "age_gate_max_years": None,
        "retain_all_versions": False,
        "linked_pms_component_id": None,
        "alert_lead_overrides": None,
        "regulatory_anchor": "MARPOL Annex I Reg 7",
        "legacy_remarks": "",
        "print_order": 10,
        "is_active": True,
        "created_at": "2026-06-24T00:00:00Z",
        "created_by": "dpa-1",
        "updated_at": "2026-06-24T00:00:00Z",
        "updated_by": "dpa-1",
    }
    row.update(overrides)
    return row


def audit_event(**overrides):
    event = {
        "audit_id": uuid.uuid4(),
        "timestamp_utc": "2026-06-25T06:45:00Z",
        "vessel_id": None,
        "actor_user_id": "dpa-1",
        "actor_role": "DPA",
        "action": "update_catalog_row",
        "entity_type": "catalog_row",
        "entity_id": "row-1",
        "before_json": '{"displayName": "Old name"}',
        "after_json": '{"displayName": "New name"}',
        "reason": "Corrected workshop spelling.",
        "event_metadata": '{"source": "api.certs.catalog.rows"}',
        "retention_tier": "hot",
        "archived_at": None,
        "schema_version": 1,
    }
    event.update(overrides)
    return event


class CertCatalogApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.factory = APIRequestFactory()
        self.reader = make_user(role="Fleet Manager", form_ids=["CERT_F_001"], process_ids=[])
        self.tracked_item_reader = make_user(role="Fleet Manager", form_ids=["CERT_F_002"], process_ids=[])
        self.dpa = make_user(role="DPA", form_ids=["CERT_F_001"], process_ids=["CERT_P_001", "CERT_P_008"])
        self.dpa_bulk = make_user(role="DPA", form_ids=["CERT_F_001"], process_ids=["CERT_P_008", "CERT_P_009"])
        self.fm_with_edit_process = make_user(role="Fleet Manager", form_ids=["CERT_F_001"], process_ids=["CERT_P_008"])

    @patch("apps.certs.views.catalog_views.repository")
    def test_sections_list_accepts_any_certs_form_reader(self, repository) -> None:
        repository.list_sections.return_value = [
            {"section_id": 2, "section_code": "STATUTORY", "display_name": "Statutory & Flag", "sort_order": 2, "active_row_count": 4}
        ]
        request = self.factory.get("/api/certs/catalog/sections/")
        force_authenticate(request, user=self.reader)

        response = CatalogSectionListView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["results"][0]["sectionCode"], "STATUTORY")

    @patch("apps.certs.views.catalog_views.repository")
    def test_catalog_read_requires_catalog_form_id(self, repository) -> None:
        request = self.factory.get("/api/certs/catalog/sections/")
        force_authenticate(request, user=self.tracked_item_reader)

        response = CatalogSectionListView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        repository.list_sections.assert_not_called()

    @patch("apps.certs.views.catalog_views.repository")
    def test_rows_list_serializes_field_map_api_keys(self, repository) -> None:
        repository.list_rows.return_value = CatalogRowPage(count=1, results=[catalog_row()])
        request = self.factory.get("/api/certs/catalog/rows/?sectionId=2&isActive=true")
        force_authenticate(request, user=self.reader)

        response = CatalogRowListCreateView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["canonicalCode"], "STAT-IOPP")
        self.assertEqual(response.data["results"][0]["applicableShipTypes"], ["all"])
        repository.list_rows.assert_called_once_with(section_id=2, is_active=True, q=None, applicable_ship_type=None)

    @patch("apps.certs.views.catalog_views.repository")
    def test_rows_list_accepts_specific_ship_type_filter(self, repository) -> None:
        repository.list_rows.return_value = CatalogRowPage(count=0, results=[])
        request = self.factory.get("/api/certs/catalog/rows/?applicableShipType=tanker")
        force_authenticate(request, user=self.reader)

        response = CatalogRowListCreateView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        repository.list_rows.assert_called_once_with(
            section_id=None,
            is_active=None,
            q=None,
            applicable_ship_type="tanker",
        )

    @patch("apps.certs.views.catalog_views.repository")
    def test_rows_list_rejects_all_as_ship_type_filter(self, repository) -> None:
        request = self.factory.get("/api/certs/catalog/rows/?applicableShipType=all")
        force_authenticate(request, user=self.reader)

        response = CatalogRowListCreateView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        repository.list_rows.assert_not_called()

    @patch("apps.certs.services.catalog_repository.connection")
    def test_repository_ship_type_filter_uses_compatibility_safe_sql(self, connection) -> None:
        cursor = MagicMock()
        cursor.description = []
        cursor.fetchone.return_value = (0,)
        cursor.fetchall.return_value = []
        connection.cursor.return_value.__enter__.return_value = cursor

        page = CatalogRepository().list_rows(applicable_ship_type="tanker")

        self.assertEqual(page.count, 0)
        executed_sql = "\n".join(call.args[0] for call in cursor.execute.call_args_list)
        self.assertNotIn("OPENJSON", executed_sql)
        self.assertIn("applicable_ship_types LIKE %s", executed_sql)
        self.assertIn('%"tanker"%', cursor.execute.call_args_list[0].args[1])

    @patch("apps.certs.services.catalog_repository.connection")
    def test_repository_catalog_audit_history_scopes_to_catalog_row_events(self, connection) -> None:
        row_id = str(uuid.uuid4())
        cursor = MagicMock()
        cursor.description = [("audit_id",), ("action",), ("entity_type",), ("entity_id",)]
        cursor.fetchall.return_value = [(uuid.uuid4(), "update_catalog_row", "catalog_row", row_id)]
        connection.cursor.return_value.__enter__.return_value = cursor

        results = CatalogRepository().list_catalog_audit_events(row_id, limit=25)

        self.assertEqual(results[0]["action"], "update_catalog_row")
        executed_sql = cursor.execute.call_args.args[0]
        self.assertIn("SELECT TOP 25", executed_sql)
        self.assertIn("entity_type = %s", executed_sql)
        self.assertIn("create_catalog_row", executed_sql)
        self.assertIn("deprecate_catalog_row", executed_sql)
        self.assertEqual(cursor.execute.call_args.args[1], ["catalog_row", row_id])

    @patch("apps.certs.views.catalog_views.record_audit_event")
    @patch("apps.certs.views.catalog_views.repository")
    def test_dpa_can_create_catalog_row_and_audit_event_is_recorded(self, repository, record_audit_event) -> None:
        created = catalog_row()
        repository.create_row.return_value = created
        request = self.factory.post(
            "/api/certs/catalog/rows/",
            {
                "canonicalCode": "STAT-IOPP",
                "sectionId": 2,
                "displayName": "International Oil Pollution Prevention Certificate",
                "printSectionLabel": "Statutory & Flag",
                "validityType": "full",
                "cadenceMonths": 60,
                "issuingAuthorityType": "flag",
                "submissionScope": "master_only",
                "reason": "Workshop seed row.",
            },
            format="json",
        )
        force_authenticate(request, user=self.dpa)

        response = CatalogRowListCreateView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["canonicalCode"], "STAT-IOPP")
        record_audit_event.assert_called_once()
        self.assertEqual(record_audit_event.call_args.kwargs["action"], "create_catalog_row")

    @patch("apps.certs.views.catalog_views.record_audit_event")
    @patch("apps.certs.views.catalog_views.repository")
    def test_dpa_inline_promotion_create_records_onboarding_context(self, repository, record_audit_event) -> None:
        created = catalog_row(
            canonical_code="FLAG-SPECIAL-PORT-STATE-LETTER",
            display_name="Special Port State Letter",
        )
        repository.create_row.return_value = created
        vessel_id = uuid.uuid4()
        batch_id = uuid.uuid4()
        request = self.factory.post(
            f"/api/certs/catalog/rows/?source=onboarding_gap_fill&vesselId={vessel_id}&batchId={batch_id}",
            {
                "canonicalCode": "FLAG-SPECIAL-PORT-STATE-LETTER",
                "sectionId": 2,
                "displayName": "Special Port State Letter",
                "printSectionLabel": "Statutory & Flag",
                "validityType": "conditional",
                "issuingAuthorityType": "flag",
                "submissionScope": "master_only",
                "applicableShipTypes": ["all"],
                "reason": "DPA added uncatalogued certificate during onboarding.",
            },
            format="json",
        )
        force_authenticate(request, user=self.dpa)

        response = CatalogRowListCreateView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        record_audit_event.assert_called_once()
        self.assertEqual(record_audit_event.call_args.kwargs["action"], "create_catalog_row")
        self.assertEqual(
            record_audit_event.call_args.kwargs["metadata"],
            {
                "source": "api.certs.catalog.inline_promotion",
                "promotionSource": "onboarding_gap_fill",
                "vesselId": str(vessel_id),
                "batchId": str(batch_id),
            },
        )
        self.assertEqual(
            record_audit_event.call_args.kwargs["reason"],
            "DPA added uncatalogued certificate during onboarding.",
        )

    @patch("apps.certs.views.catalog_views.repository")
    def test_create_rejects_unknown_applicable_ship_type(self, repository) -> None:
        request = self.factory.post(
            "/api/certs/catalog/rows/",
            {
                "canonicalCode": "STAT-IOPP",
                "sectionId": 2,
                "displayName": "International Oil Pollution Prevention Certificate",
                "printSectionLabel": "Statutory & Flag",
                "validityType": "full",
                "issuingAuthorityType": "flag",
                "submissionScope": "master_only",
                "applicableShipTypes": ["cruise_ship"],
            },
            format="json",
        )
        force_authenticate(request, user=self.dpa)

        response = CatalogRowListCreateView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        repository.create_row.assert_not_called()

    @patch("apps.certs.views.catalog_views.repository")
    def test_create_rejects_iopp_form_variant_catalog_rows(self, repository) -> None:
        for code in ("STAT-IOPP-A", "STAT-IOPP-B"):
            with self.subTest(code=code):
                request = self.factory.post(
                    "/api/certs/catalog/rows/",
                    {
                        "canonicalCode": code,
                        "sectionId": 2,
                        "displayName": "International Oil Pollution Prevention Certificate",
                        "printSectionLabel": "Statutory & Flag",
                        "validityType": "full",
                        "issuingAuthorityType": "flag",
                        "submissionScope": "master_only",
                    },
                    format="json",
                )
                force_authenticate(request, user=self.dpa)

                response = CatalogRowListCreateView.as_view()(request)

                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
                self.assertEqual(
                    str(response.data["canonicalCode"][0]),
                    "Model IOPP Form A/B on tracked-item formVariant; keep one STAT-IOPP catalog row.",
                )
        repository.create_row.assert_not_called()

    @patch("apps.certs.views.catalog_views.repository")
    def test_create_specific_vessel_mode_requires_vessel_ids(self, repository) -> None:
        request = self.factory.post(
            "/api/certs/catalog/rows/",
            {
                "canonicalCode": "STAT-IOPP",
                "sectionId": 2,
                "displayName": "International Oil Pollution Prevention Certificate",
                "printSectionLabel": "Statutory & Flag",
                "validityType": "full",
                "issuingAuthorityType": "flag",
                "submissionScope": "master_only",
                "applicabilityMode": "specific_vessel_ids",
                "specificVesselIds": [],
            },
            format="json",
        )
        force_authenticate(request, user=self.dpa)

        response = CatalogRowListCreateView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        repository.create_row.assert_not_called()

    @patch("apps.certs.views.catalog_views.repository")
    def test_create_rejects_missing_parent_row(self, repository) -> None:
        parent_id = uuid.uuid4()
        repository.get_row.return_value = None
        request = self.factory.post(
            "/api/certs/catalog/rows/",
            {
                "canonicalCode": "STAT-IOPP-ANNUAL-SURVEY",
                "sectionId": 2,
                "displayName": "IOPP Annual Survey",
                "printSectionLabel": "Statutory & Flag",
                "validityType": "conditional",
                "issuingAuthorityType": "class",
                "submissionScope": "master_only",
                "parentId": str(parent_id),
            },
            format="json",
        )
        force_authenticate(request, user=self.dpa)

        response = CatalogRowListCreateView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["parentId"], "Parent catalog row was not found.")
        repository.create_row.assert_not_called()

    @patch("apps.certs.views.catalog_views.repository")
    def test_create_rejects_parent_that_is_already_a_child(self, repository) -> None:
        parent_id = uuid.uuid4()
        grandparent_id = uuid.uuid4()
        repository.get_row.return_value = catalog_row(catalog_id=parent_id, parent_id=grandparent_id)
        request = self.factory.post(
            "/api/certs/catalog/rows/",
            {
                "canonicalCode": "STAT-IOPP-ANNUAL-SURVEY-DETAIL",
                "sectionId": 2,
                "displayName": "IOPP Annual Survey Sub-row",
                "printSectionLabel": "Statutory & Flag",
                "validityType": "conditional",
                "issuingAuthorityType": "class",
                "submissionScope": "master_only",
                "parentId": str(parent_id),
            },
            format="json",
        )
        force_authenticate(request, user=self.dpa)

        response = CatalogRowListCreateView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["parentId"], "Catalog Admin supports only one child level in V1.")
        repository.create_row.assert_not_called()

    @patch("apps.certs.views.catalog_views.repository")
    def test_fm_with_catalog_edit_process_still_cannot_write_catalog(self, repository) -> None:
        request = self.factory.post(
            "/api/certs/catalog/rows/",
            {
                "canonicalCode": "STAT-IOPP",
                "sectionId": 2,
                "displayName": "International Oil Pollution Prevention Certificate",
                "printSectionLabel": "Statutory & Flag",
                "validityType": "full",
                "issuingAuthorityType": "flag",
                "submissionScope": "master_only",
            },
            format="json",
        )
        force_authenticate(request, user=self.fm_with_edit_process)

        response = CatalogRowListCreateView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        repository.create_row.assert_not_called()

    @patch("apps.certs.views.catalog_views.repository")
    def test_catalog_row_audit_history_returns_field_map_keys(self, repository) -> None:
        row_id = uuid.uuid4()
        repository.get_row.return_value = catalog_row(catalog_id=row_id)
        repository.list_catalog_audit_events.return_value = [
            audit_event(entity_id=str(row_id)),
        ]
        request = self.factory.get(f"/api/certs/catalog/rows/{row_id}/audit/")
        force_authenticate(request, user=self.reader)

        response = CatalogRowAuditHistoryView.as_view()(request, catalog_id=row_id)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["results"][0]["action"], "update_catalog_row")
        self.assertEqual(response.data["results"][0]["actorUserId"], "dpa-1")
        self.assertEqual(response.data["results"][0]["before"]["displayName"], "Old name")
        self.assertEqual(response.data["results"][0]["after"]["displayName"], "New name")
        self.assertEqual(response.data["results"][0]["eventMetadata"]["source"], "api.certs.catalog.rows")
        repository.list_catalog_audit_events.assert_called_once_with(str(row_id))

    @patch("apps.certs.views.catalog_views.repository")
    def test_catalog_row_audit_history_requires_catalog_form_id(self, repository) -> None:
        row_id = uuid.uuid4()
        request = self.factory.get(f"/api/certs/catalog/rows/{row_id}/audit/")
        force_authenticate(request, user=self.tracked_item_reader)

        response = CatalogRowAuditHistoryView.as_view()(request, catalog_id=row_id)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        repository.list_catalog_audit_events.assert_not_called()

    @patch("apps.certs.views.catalog_views.repository")
    def test_catalog_row_detail_accepts_canonical_code_identifier(self, repository) -> None:
        row_id = uuid.uuid4()
        repository.get_row.return_value = None
        repository.get_row_by_code.return_value = catalog_row(catalog_id=row_id, canonical_code="STAT-IOPP")
        request = self.factory.get("/api/certs/catalog/rows/STAT-IOPP/")
        force_authenticate(request, user=self.reader)

        response = CatalogRowDetailView.as_view()(request, catalog_id="STAT-IOPP")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], str(row_id))
        self.assertEqual(response.data["canonicalCode"], "STAT-IOPP")
        repository.get_row.assert_called_once_with("STAT-IOPP")
        repository.get_row_by_code.assert_called_once_with("STAT-IOPP")

    @patch("apps.certs.views.catalog_views.repository")
    def test_catalog_row_audit_history_accepts_canonical_code_identifier(self, repository) -> None:
        row_id = uuid.uuid4()
        repository.get_row.return_value = None
        repository.get_row_by_code.return_value = catalog_row(catalog_id=row_id, canonical_code="STAT-IOPP")
        repository.list_catalog_audit_events.return_value = [audit_event(entity_id=str(row_id))]
        request = self.factory.get("/api/certs/catalog/rows/STAT-IOPP/audit/")
        force_authenticate(request, user=self.reader)

        response = CatalogRowAuditHistoryView.as_view()(request, catalog_id="STAT-IOPP")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        repository.list_catalog_audit_events.assert_called_once_with(str(row_id))

    @patch("apps.certs.views.catalog_views.record_audit_event")
    @patch("apps.certs.views.catalog_views.repository")
    def test_dpa_can_update_catalog_row_and_audit_event_is_recorded(self, repository, record_audit_event) -> None:
        row_id = uuid.uuid4()
        before = catalog_row(catalog_id=row_id, display_name="Old name")
        after = catalog_row(catalog_id=row_id, display_name="New name")
        repository.update_row.return_value = (before, after)
        request = self.factory.patch(
            f"/api/certs/catalog/rows/{row_id}/",
            {"displayName": "New name", "reason": "Corrected workshop spelling."},
            format="json",
        )
        force_authenticate(request, user=self.dpa)

        response = CatalogRowDetailView.as_view()(request, catalog_id=row_id)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["displayName"], "New name")
        record_audit_event.assert_called_once()
        self.assertEqual(record_audit_event.call_args.kwargs["action"], "update_catalog_row")

    @patch("apps.certs.views.catalog_views.record_audit_event")
    @patch("apps.certs.views.catalog_views.repository")
    def test_dpa_can_deprecate_catalog_row_with_reason(self, repository, record_audit_event) -> None:
        row_id = uuid.uuid4()
        before = catalog_row(catalog_id=row_id, is_active=True)
        after = catalog_row(catalog_id=row_id, is_active=False)
        repository.get_row.return_value = before
        repository.update_row.return_value = (before, after)
        request = self.factory.post(
            f"/api/certs/catalog/rows/{row_id}/deprecate/",
            {"reason": "Superseded by revised flag-state certificate type."},
            format="json",
        )
        force_authenticate(request, user=self.dpa)

        response = CatalogRowDeprecateView.as_view()(request, catalog_id=row_id)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data["isActive"])
        repository.update_row.assert_called_once_with(
            str(row_id),
            {"isActive": False},
            actor_id="dpa-1",
        )
        record_audit_event.assert_called_once()
        self.assertEqual(record_audit_event.call_args.kwargs["action"], "deprecate_catalog_row")
        self.assertEqual(record_audit_event.call_args.kwargs["before"]["isActive"], True)
        self.assertEqual(record_audit_event.call_args.kwargs["after"]["isActive"], False)

    @patch("apps.certs.views.catalog_views.record_audit_event")
    @patch("apps.certs.views.catalog_views.repository")
    def test_deprecate_requires_reason(self, repository, record_audit_event) -> None:
        row_id = uuid.uuid4()
        repository.get_row.return_value = catalog_row(catalog_id=row_id, is_active=True)
        request = self.factory.post(
            f"/api/certs/catalog/rows/{row_id}/deprecate/",
            {"reason": "   "},
            format="json",
        )
        force_authenticate(request, user=self.dpa)

        response = CatalogRowDeprecateView.as_view()(request, catalog_id=row_id)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["reason"], "Deprecation reason is required.")
        repository.update_row.assert_not_called()
        record_audit_event.assert_not_called()

    @patch("apps.certs.views.catalog_views.repository")
    def test_fm_cannot_deprecate_catalog_row(self, repository) -> None:
        row_id = uuid.uuid4()
        request = self.factory.post(
            f"/api/certs/catalog/rows/{row_id}/deprecate/",
            {"reason": "Superseded by revised flag-state certificate type."},
            format="json",
        )
        force_authenticate(request, user=self.fm_with_edit_process)

        response = CatalogRowDeprecateView.as_view()(request, catalog_id=row_id)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        repository.update_row.assert_not_called()

    @patch("apps.certs.views.catalog_views.record_audit_event")
    @patch("apps.certs.views.catalog_views.repository")
    def test_dpa_can_bulk_soft_delete_up_to_50_rows_with_reason(self, repository, record_audit_event) -> None:
        row_ids = [uuid.uuid4(), uuid.uuid4()]
        before_rows = [catalog_row(catalog_id=row_ids[0], is_active=True), catalog_row(catalog_id=row_ids[1], is_active=True)]
        after_rows = [catalog_row(catalog_id=row_ids[0], is_active=False), catalog_row(catalog_id=row_ids[1], is_active=False)]
        repository.bulk_soft_delete_rows.return_value = list(zip(before_rows, after_rows))
        request = self.factory.post(
            "/api/certs/catalog/rows/bulk-soft-delete/",
            {
                "catalogIds": [str(row_id) for row_id in row_ids],
                "reason": "Superseded duplicate workshop rows.",
            },
            format="json",
        )
        force_authenticate(request, user=self.dpa_bulk)

        response = CatalogRowBulkSoftDeleteView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["updatedCount"], 2)
        repository.bulk_soft_delete_rows.assert_called_once_with(
            [str(row_id) for row_id in row_ids],
            actor_id="dpa-1",
        )
        self.assertEqual(record_audit_event.call_count, 2)
        self.assertEqual(record_audit_event.call_args_list[0].kwargs["action"], "bulk_soft_delete")
        self.assertEqual(record_audit_event.call_args_list[0].kwargs["before"]["isActive"], True)
        self.assertEqual(record_audit_event.call_args_list[0].kwargs["after"]["isActive"], False)
        self.assertEqual(
            record_audit_event.call_args_list[0].kwargs["metadata"],
            {
                "source": "api.certs.catalog.rows.bulk_soft_delete",
                "batchSize": 2,
                "catalogIds": [str(row_id) for row_id in row_ids],
            },
        )

    @patch("apps.certs.views.catalog_views.repository")
    def test_bulk_soft_delete_rejects_more_than_50_rows(self, repository) -> None:
        request = self.factory.post(
            "/api/certs/catalog/rows/bulk-soft-delete/",
            {
                "catalogIds": [str(uuid.uuid4()) for _ in range(51)],
                "reason": "Superseded duplicate workshop rows.",
            },
            format="json",
        )
        force_authenticate(request, user=self.dpa_bulk)

        response = CatalogRowBulkSoftDeleteView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["catalogIds"], "Bulk soft-delete is capped at 50 rows per batch.")
        repository.bulk_soft_delete_rows.assert_not_called()

    @patch("apps.certs.views.catalog_views.repository")
    def test_bulk_soft_delete_requires_reason_minimum_length(self, repository) -> None:
        request = self.factory.post(
            "/api/certs/catalog/rows/bulk-soft-delete/",
            {"catalogIds": [str(uuid.uuid4())], "reason": "short"},
            format="json",
        )
        force_authenticate(request, user=self.dpa_bulk)

        response = CatalogRowBulkSoftDeleteView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["reason"], "Reason must be at least 10 characters.")
        repository.bulk_soft_delete_rows.assert_not_called()

    @patch("apps.certs.views.catalog_views.repository")
    def test_fm_cannot_bulk_soft_delete_even_with_bulk_process(self, repository) -> None:
        fm_bulk = make_user(role="Fleet Manager", form_ids=["CERT_F_001"], process_ids=["CERT_P_009"])
        request = self.factory.post(
            "/api/certs/catalog/rows/bulk-soft-delete/",
            {
                "catalogIds": [str(uuid.uuid4())],
                "reason": "Superseded duplicate workshop rows.",
            },
            format="json",
        )
        force_authenticate(request, user=fm_bulk)

        response = CatalogRowBulkSoftDeleteView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        repository.bulk_soft_delete_rows.assert_not_called()

    @patch("apps.certs.views.catalog_views.record_audit_event")
    @patch("apps.certs.views.catalog_views.repository")
    def test_dpa_can_hard_purge_catalog_row_with_reason(self, repository, record_audit_event) -> None:
        row_id = uuid.uuid4()
        before = catalog_row(catalog_id=row_id, is_active=False)
        repository.delete_row.return_value = before
        request = self.factory.delete(
            f"/api/certs/catalog/rows/{row_id}/",
            {"reason": "Retention window expired for duplicate catalog row."},
            format="json",
        )
        force_authenticate(request, user=self.dpa_bulk)

        response = CatalogRowHardPurgeView.as_view()(request, catalog_id=row_id)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        repository.delete_row.assert_called_once_with(str(row_id))
        record_audit_event.assert_called_once()
        self.assertEqual(record_audit_event.call_args.kwargs["action"], "hard_purge_catalog_row")
        self.assertEqual(record_audit_event.call_args.kwargs["before"]["id"], str(row_id))
        self.assertIsNone(record_audit_event.call_args.kwargs["after"])
        self.assertEqual(
            record_audit_event.call_args.kwargs["metadata"],
            {"source": "api.certs.catalog.rows.hard_purge"},
        )

    @patch("apps.certs.views.catalog_views.repository")
    def test_hard_purge_requires_bulk_action_process(self, repository) -> None:
        row_id = uuid.uuid4()
        request = self.factory.delete(
            f"/api/certs/catalog/rows/{row_id}/",
            {"reason": "Retention window expired for duplicate catalog row."},
            format="json",
        )
        force_authenticate(request, user=self.dpa)

        response = CatalogRowHardPurgeView.as_view()(request, catalog_id=row_id)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        repository.delete_row.assert_not_called()

    @patch("apps.certs.views.catalog_views.record_audit_event")
    @patch("apps.certs.views.catalog_views.repository")
    def test_dpa_can_create_dynamic_instance_parent_row(self, repository, record_audit_event) -> None:
        created = catalog_row(
            canonical_code="EQ-SCBA-ELSA-EEBD",
            display_name="SCBA / ELSA / EEBD",
            parent_supports_dynamic_children=True,
        )
        repository.create_row.return_value = created
        request = self.factory.post(
            "/api/certs/catalog/rows/",
            {
                "canonicalCode": "EQ-SCBA-ELSA-EEBD",
                "sectionId": 4,
                "displayName": "SCBA / ELSA / EEBD",
                "printSectionLabel": "Equipment LSA/FFA/Nav/GMDSS",
                "validityType": "conditional",
                "cadenceMonths": 12,
                "issuingAuthorityType": "company",
                "submissionScope": "master_only",
                "parentSupportsDynamicChildren": True,
                "reason": "Phase 1.6 dynamic-instance equipment parent.",
            },
            format="json",
        )
        force_authenticate(request, user=self.dpa)

        response = CatalogRowListCreateView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data["parentSupportsDynamicChildren"])
        self.assertTrue(repository.create_row.call_args.args[0]["parentSupportsDynamicChildren"])
        record_audit_event.assert_called_once()
        self.assertEqual(record_audit_event.call_args.kwargs["action"], "create_catalog_row")

    @patch("apps.certs.views.catalog_views.record_audit_event")
    @patch("apps.certs.views.catalog_views.repository")
    def test_dpa_can_store_inert_type_approval_pms_component_id(self, repository, record_audit_event) -> None:
        created = catalog_row(
            canonical_code="TYPE-OWS-APPROVAL",
            section_id=7,
            section_code="TYPE_APPROVAL",
            section_name="Type Approvals",
            display_name="OWS Type Approval",
            validity_type="permanent",
            cadence_months=None,
            linked_pms_component_id="PMS-COMP-OWS-001",
        )
        repository.create_row.return_value = created
        request = self.factory.post(
            "/api/certs/catalog/rows/",
            {
                "canonicalCode": "TYPE-OWS-APPROVAL",
                "sectionId": 7,
                "displayName": "OWS Type Approval",
                "printSectionLabel": "Type Approvals",
                "validityType": "permanent",
                "cadenceMonths": None,
                "issuingAuthorityType": "manufacturer",
                "submissionScope": "all_ranks_with_approval",
                "linkedPmsComponentId": "PMS-COMP-OWS-001",
                "reason": "Link PMS component reference for future manual refresh alert.",
            },
            format="json",
        )
        force_authenticate(request, user=self.dpa)

        response = CatalogRowListCreateView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["linkedPmsComponentId"], "PMS-COMP-OWS-001")
        self.assertEqual(repository.create_row.call_args.args[0]["linkedPmsComponentId"], "PMS-COMP-OWS-001")
        record_audit_event.assert_called_once()

    @patch("apps.certs.views.catalog_views.repository")
    def test_create_rejects_tonnage_tax_outside_trade_section(self, repository) -> None:
        request = self.factory.post(
            "/api/certs/catalog/rows/",
            {
                "canonicalCode": "STAT-TONNAGE-TAX",
                "sectionId": 2,
                "displayName": "Tonnage Tax",
                "printSectionLabel": "Statutory & Flag",
                "validityType": "conditional",
                "issuingAuthorityType": "flag",
                "submissionScope": "all_ranks_with_approval",
            },
            format="json",
        )
        force_authenticate(request, user=self.dpa)

        response = CatalogRowListCreateView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(str(response.data["sectionId"][0]), "Tonnage Tax catalog rows must stay in Trade & Commercial.")
        repository.create_row.assert_not_called()

    @patch("apps.certs.views.catalog_views.repository")
    def test_create_rejects_catalog_level_tonnage_tax_cadence(self, repository) -> None:
        request = self.factory.post(
            "/api/certs/catalog/rows/",
            {
                "canonicalCode": "TRADE-TONNAGE-TAX",
                "sectionId": 3,
                "displayName": "Tonnage Tax",
                "printSectionLabel": "Trade & Commercial",
                "validityType": "conditional",
                "cadenceMonths": 12,
                "issuingAuthorityType": "flag",
                "submissionScope": "all_ranks_with_approval",
            },
            format="json",
        )
        force_authenticate(request, user=self.dpa)

        response = CatalogRowListCreateView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            str(response.data["cadenceMonths"][0]),
            "Tonnage Tax cadence is configured per vessel on TrackedItem, not on the catalog row.",
        )
        repository.create_row.assert_not_called()

    @patch("apps.certs.views.catalog_views.record_audit_event")
    @patch("apps.certs.views.catalog_views.repository")
    def test_patch_rejects_catalog_level_tonnage_tax_cadence(self, repository, record_audit_event) -> None:
        row_id = uuid.uuid4()
        repository.get_row.return_value = catalog_row(
            catalog_id=row_id,
            canonical_code="TRADE-TONNAGE-TAX",
            section_id=3,
            section_code="TRADE",
            section_name="Trade & Commercial",
            display_name="Tonnage Tax",
            cadence_months=None,
        )
        request = self.factory.patch(
            f"/api/certs/catalog/rows/{row_id}/",
            {"cadenceMonths": 12},
            format="json",
        )
        force_authenticate(request, user=self.dpa)

        response = CatalogRowDetailView.as_view()(request, catalog_id=row_id)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            str(response.data["cadenceMonths"][0]),
            "Tonnage Tax cadence is configured per vessel on TrackedItem, not on the catalog row.",
        )
        repository.update_row.assert_not_called()
        record_audit_event.assert_not_called()

    @patch("apps.certs.views.catalog_views.repository")
    def test_create_rejects_dynamic_flag_on_child_catalog_row(self, repository) -> None:
        parent_id = uuid.uuid4()
        repository.get_row.return_value = catalog_row(catalog_id=parent_id, parent_id=None)
        request = self.factory.post(
            "/api/certs/catalog/rows/",
            {
                "canonicalCode": "EQ-SCBA-CYLINDER-GROUP-1",
                "sectionId": 4,
                "displayName": "SCBA Cylinder Hydro Test Group 1",
                "printSectionLabel": "Equipment LSA/FFA/Nav/GMDSS",
                "validityType": "conditional",
                "issuingAuthorityType": "company",
                "submissionScope": "master_only",
                "parentId": str(parent_id),
                "parentSupportsDynamicChildren": True,
            },
            format="json",
        )
        force_authenticate(request, user=self.dpa)

        response = CatalogRowListCreateView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data["parentSupportsDynamicChildren"],
            "Only top-level catalog parent rows can support dynamic child TrackedItems.",
        )
        repository.create_row.assert_not_called()

    @patch("apps.certs.views.catalog_views.repository")
    def test_create_rejects_dynamic_flag_on_portable_rollup_row(self, repository) -> None:
        request = self.factory.post(
            "/api/certs/catalog/rows/",
            {
                "canonicalCode": "EQ-PORTABLE-FIRE-EXTINGUISHERS",
                "sectionId": 4,
                "displayName": "Portable Fire Extinguishers Annual Service",
                "printSectionLabel": "Equipment LSA/FFA/Nav/GMDSS",
                "validityType": "conditional",
                "cadenceMonths": 12,
                "issuingAuthorityType": "company",
                "submissionScope": "master_only",
                "parentSupportsDynamicChildren": True,
            },
            format="json",
        )
        force_authenticate(request, user=self.dpa)

        response = CatalogRowListCreateView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            str(response.data["parentSupportsDynamicChildren"][0]),
            "Portable equipment roll-up rows must stay one TrackedItem per vessel; keep per-unit detail in the service report PDF.",
        )
        repository.create_row.assert_not_called()

    @patch("apps.certs.views.catalog_views.record_audit_event")
    @patch("apps.certs.views.catalog_views.repository")
    def test_patch_all_matching_mode_clears_specific_vessel_ids(self, repository, record_audit_event) -> None:
        row_id = uuid.uuid4()
        before = catalog_row(catalog_id=row_id, applicability_mode="specific_vessel_ids", specific_vessel_ids=f'["{uuid.uuid4()}"]')
        after = catalog_row(catalog_id=row_id, applicability_mode="all_matching_type", specific_vessel_ids="[]")
        repository.update_row.return_value = (before, after)
        request = self.factory.patch(
            f"/api/certs/catalog/rows/{row_id}/",
            {"applicabilityMode": "all_matching_type"},
            format="json",
        )
        force_authenticate(request, user=self.dpa)

        response = CatalogRowDetailView.as_view()(request, catalog_id=row_id)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        repository.update_row.assert_called_once()
        self.assertEqual(repository.update_row.call_args.args[1]["specificVesselIds"], [])

    @patch("apps.certs.views.catalog_views.record_audit_event")
    @patch("apps.certs.views.catalog_views.repository")
    def test_patch_rejects_self_parent(self, repository, record_audit_event) -> None:
        row_id = uuid.uuid4()
        request = self.factory.patch(
            f"/api/certs/catalog/rows/{row_id}/",
            {"parentId": str(row_id)},
            format="json",
        )
        force_authenticate(request, user=self.dpa)

        response = CatalogRowDetailView.as_view()(request, catalog_id=row_id)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["parentId"], "A catalog row cannot be its own parent.")
        repository.update_row.assert_not_called()
        record_audit_event.assert_not_called()

    @patch("apps.certs.views.catalog_views.record_audit_event")
    @patch("apps.certs.views.catalog_views.repository")
    def test_patch_rejects_dynamic_flag_on_existing_child_row(self, repository, record_audit_event) -> None:
        row_id = uuid.uuid4()
        parent_id = uuid.uuid4()
        repository.get_row.return_value = catalog_row(catalog_id=row_id, parent_id=parent_id)
        request = self.factory.patch(
            f"/api/certs/catalog/rows/{row_id}/",
            {"parentSupportsDynamicChildren": True},
            format="json",
        )
        force_authenticate(request, user=self.dpa)

        response = CatalogRowDetailView.as_view()(request, catalog_id=row_id)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data["parentSupportsDynamicChildren"],
            "Only top-level catalog parent rows can support dynamic child TrackedItems.",
        )
        repository.update_row.assert_not_called()
        record_audit_event.assert_not_called()

    @patch("apps.certs.views.catalog_views.record_audit_event")
    @patch("apps.certs.views.catalog_views.repository")
    def test_patch_rejects_moving_parent_with_children_under_another_parent(self, repository, record_audit_event) -> None:
        row_id = uuid.uuid4()
        parent_id = uuid.uuid4()
        repository.get_row.return_value = catalog_row(catalog_id=parent_id, parent_id=None)
        repository.has_children.return_value = True
        request = self.factory.patch(
            f"/api/certs/catalog/rows/{row_id}/",
            {"parentId": str(parent_id)},
            format="json",
        )
        force_authenticate(request, user=self.dpa)

        response = CatalogRowDetailView.as_view()(request, catalog_id=row_id)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["parentId"], "Rows that already have children cannot be moved under a parent in V1.")
        repository.update_row.assert_not_called()
        record_audit_event.assert_not_called()
