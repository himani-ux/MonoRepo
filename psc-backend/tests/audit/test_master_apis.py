from __future__ import annotations

import importlib
import unittest
from datetime import date, datetime
from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from uuid import UUID

from django.urls import resolve
from rest_framework.test import APIRequestFactory, force_authenticate

from apps.inspection.audit.models import MasterAuditQualifiedAuditor
from apps.inspection.audit.serializers.masters import (
    AuditQualifyingBodySerializer,
    ExternalAuditOrgSerializer,
    HodAssignmentSerializer,
    QualifiedAuditorSerializer,
    VesselRoDelegationSerializer,
)
from apps.inspection.audit.services.auditor_selection import resolve_user_identity
from apps.inspection.audit.permissions import AUDIT_P_009, AUDIT_P_013
from apps.inspection.audit.views.masters import (
    AuditQualifyingBodyListCreateView,
    ExternalAuditOrgListCreateView,
    OfficeUserLookupView,
    QualifiedAuditorDetailView,
    QualifiedAuditorListCreateView,
    _office_user_lookup_rows,
)


class AuditMasterApiContractTests(unittest.TestCase):
    def test_master_api_requires_authentication_and_process_gate(self):
        factory = APIRequestFactory()
        view = ExternalAuditOrgListCreateView.as_view()

        unauthenticated = view(factory.get("/api/audit/masters/external-audit-orgs/"))
        self.assertEqual(unauthenticated.status_code, 401)

        request = factory.get("/api/audit/masters/external-audit-orgs/")
        user = SimpleNamespace(
            is_authenticated=True,
            id="master-1",
            role="MASTER",
            process_ids=[],
        )
        force_authenticate(request, user=user)
        denied = view(request)
        self.assertEqual(denied.status_code, 403)

    @patch.object(ExternalAuditOrgListCreateView, "get_queryset")
    def test_external_audit_registration_permission_can_read_active_external_orgs(self, get_queryset):
        get_queryset.return_value = [
            SimpleNamespace(
                id=UUID("44444444-4444-4444-8444-444444444444"),
                name="DNV",
                org_type="CLASS_SOCIETY",
                country="Norway",
                linked_class_society_ref=None,
                is_active=True,
                created_by="seed",
                created_date=datetime(2026, 8, 19, 12, 0),
            )
        ]
        factory = APIRequestFactory()
        view = ExternalAuditOrgListCreateView.as_view()
        user = SimpleNamespace(
            is_authenticated=True,
            id="external-register",
            role="DPA",
            process_ids=[AUDIT_P_013],
        )

        request = factory.get("/api/audit/masters/external-audit-orgs/")
        force_authenticate(request, user=user)
        response = view(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["data"]["count"], 1)
        self.assertEqual(response.data["data"]["results"][0]["name"], "DNV")

        create_request = factory.post(
            "/api/audit/masters/external-audit-orgs/",
            {"name": "New RO", "org_type": "RO"},
            format="json",
        )
        force_authenticate(create_request, user=user)
        denied = view(create_request)
        self.assertEqual(denied.status_code, 403)

    def test_qualifying_body_api_uses_audit_master_permission_gate(self):
        factory = APIRequestFactory()
        view = AuditQualifyingBodyListCreateView.as_view()

        unauthenticated = view(factory.get("/api/audit/masters/qualifying-bodies/"))
        self.assertEqual(unauthenticated.status_code, 401)

        request = factory.get("/api/audit/masters/qualifying-bodies/")
        user = SimpleNamespace(
            is_authenticated=True,
            id="master-1",
            role="MASTER",
            process_ids=[],
        )
        force_authenticate(request, user=user)
        denied = view(request)
        self.assertEqual(denied.status_code, 403)

    def test_master_routes_are_registered(self):
        self.assertEqual(resolve("/api/audit/masters/qualified-auditors/").url_name, "audit-master-qualified-auditors")
        self.assertEqual(resolve("/api/audit/masters/qualifying-bodies/").url_name, "audit-master-qualifying-bodies")
        self.assertEqual(
            resolve("/api/audit/masters/qualifying-bodies/11111111-1111-1111-1111-111111111111/").url_name,
            "audit-master-qualifying-body-detail",
        )
        self.assertEqual(resolve("/api/audit/masters/office-users/").url_name, "audit-master-office-users")
        self.assertEqual(resolve("/api/audit/masters/external-audit-orgs/").url_name, "audit-master-external-audit-orgs")
        self.assertEqual(resolve("/api/audit/masters/ro-delegations/").url_name, "audit-master-ro-delegations")
        self.assertEqual(resolve("/api/audit/admin/hod-coverage/").url_name, "audit-hod-coverage")

    @patch("apps.inspection.audit.views.masters._office_user_lookup_rows")
    def test_office_user_lookup_returns_active_user_role_details(self, lookup_rows):
        lookup_rows.return_value = [
            {
                "employee_id": "EMP001",
                "display_name": "Capt. Harman Sandhu",
                "employee_name": "Harman Sandhu",
                "username": "Harman.S",
                "employee_role": "Internal",
                "department": "Marine",
                "role_name": "SEQ Manager",
            }
        ]
        request = APIRequestFactory().get("/api/audit/masters/office-users/")
        user = SimpleNamespace(
            is_authenticated=True,
            id="audit-admin",
            user_type="OFFICE",
            role="OFFICE_PIC",
            process_ids=[AUDIT_P_009],
        )
        force_authenticate(request, user=user)

        response = OfficeUserLookupView.as_view()(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["data"]["count"], 1)
        self.assertEqual(response.data["data"]["results"][0]["employee_id"], "EMP001")
        self.assertEqual(response.data["data"]["results"][0]["employee_role"], "Internal")
        self.assertEqual(response.data["data"]["results"][0]["role_name"], "SEQ Manager")

    @patch("apps.inspection.audit.views.masters.OfficeUser.objects")
    @patch("apps.inspection.audit.views.masters.connection.cursor")
    def test_office_user_lookup_resolves_master_role_with_raw_join(self, cursor_factory, office_objects):
        class FakeOfficeUserQueryset:
            def values(self, *fields):
                return [
                    {
                        "employee_id": "Harman.S",
                        "display_name": "Capt. Harman Sandhu",
                        "employee_name": "Harman Sandhu",
                        "username": "Harman.S",
                        "employee_role": "Internal",
                        "department": "Marine",
                    }
                ]

        office_objects.filter.return_value = FakeOfficeUserQueryset()
        cursor = MagicMock()
        cursor.fetchone.return_value = ("SEQ Manager",)
        cursor_context = MagicMock()
        cursor_context.__enter__.return_value = cursor
        cursor_factory.return_value = cursor_context

        rows = _office_user_lookup_rows()

        self.assertEqual(rows[0]["role_name"], "SEQ Manager")
        sql, params = cursor.execute.call_args.args
        self.assertIn("mapping_role_user", sql)
        self.assertIn("master_role", sql)
        self.assertEqual(params, ["Harman.S"])

    @patch("apps.inspection.audit.views.masters._office_role_names_by_identifier")
    @patch("apps.inspection.audit.views.masters.OfficeUser.objects")
    def test_office_user_lookup_excludes_users_without_master_role(self, office_objects, role_lookup):
        class FakeOfficeUserQueryset:
            def values(self, *fields):
                return [
                    {
                        "employee_id": "Harman.S",
                        "display_name": "Capt. Harman Sandhu",
                        "employee_name": "Harman Sandhu",
                        "username": "Harman.S",
                        "employee_role": "Internal",
                        "department": "Marine",
                    },
                    {
                        "employee_id": "NoRole.User",
                        "display_name": "No Role User",
                        "employee_name": "No Role",
                        "username": "NoRole.User",
                        "employee_role": "Internal",
                        "department": "Marine",
                    },
                ]

        office_objects.filter.return_value = FakeOfficeUserQueryset()
        role_lookup.return_value = {"harman.s": "SEQ Manager"}

        rows = _office_user_lookup_rows()

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["employee_id"], "Harman.S")
        self.assertEqual(rows[0]["role_name"], "SEQ Manager")

    def test_resolve_user_identity_uses_master_role_for_actual_designation(self):
        class FakeCursor:
            def __init__(self):
                self.calls = []

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, traceback):
                return False

            def execute(self, sql, params=None):
                self.calls.append((sql, params or []))

            def fetchone(self):
                return ("SEQ Manager",)

        office_user = SimpleNamespace(
            employee_id="KSM001",
            username="Harman.S",
            display_name="Capt. Harman Sandhu",
            employee_name="",
            full_name="",
            employee_role="Internal",
            department="SEQ",
        )
        office_queryset = MagicMock()
        office_queryset.filter.return_value.first.return_value = office_user
        cursor = FakeCursor()

        with (
            patch("apps.inspection.audit.services.auditor_selection.OfficeUser.objects") as office_objects,
            patch(
                "apps.inspection.audit.services.auditor_selection.connection",
                SimpleNamespace(vendor="microsoft", cursor=lambda: cursor),
            ),
        ):
            office_objects.filter.return_value = office_queryset
            identity = resolve_user_identity("KSM001")

        self.assertEqual(identity["name"], "Capt. Harman Sandhu")
        self.assertEqual(identity["designation"], "SEQ Manager")
        self.assertNotEqual(identity["designation"], "Internal")
        self.assertIn("master_role", cursor.calls[0][0])

    def test_external_org_serializer_normalizes_type(self):
        serializer = ExternalAuditOrgSerializer(
            data={"name": "ABS", "org_type": "ro", "is_active": True}
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(serializer.validated_data["org_type"], "RO")

    def test_qualifying_body_serializer_trims_name(self):
        serializer = AuditQualifyingBodySerializer(
            data={"body_name": "  KSM Academy  ", "is_active": True, "is_deleted": False}
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(serializer.validated_data["body_name"], "KSM Academy")

    def test_qualifying_body_serializer_rejects_blank_name(self):
        serializer = AuditQualifyingBodySerializer(
            data={"body_name": "   ", "is_active": True, "is_deleted": False}
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("body_name", serializer.errors)

    def test_qualifying_body_migration_seed_uses_database_uuid_default(self):
        migration = importlib.import_module("apps.inspection.migrations.0026_audit_qualifying_body_master")

        class FakeCursor:
            def __init__(self):
                self.calls = []

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, traceback):
                return False

            def execute(self, sql, params=None):
                self.calls.append((sql, params or []))

            def fetchall(self):
                return [("Existing Body",)]

        cursor = FakeCursor()
        schema_editor = SimpleNamespace(
            connection=SimpleNamespace(
                vendor="microsoft",
                cursor=lambda: cursor,
            )
        )

        migration.seed_qualifying_bodies(SimpleNamespace(), schema_editor)

        insert_calls = [call for call in cursor.calls if "INSERT INTO dbo.aud_master_qual_body" in call[0]]
        self.assertTrue(insert_calls)
        self.assertTrue(all("id," not in call[0] for call in insert_calls))
        self.assertTrue(any(call[1][0] == "Existing Body" for call in insert_calls))

    def test_qualified_auditor_create_uses_sql_server_uuid_casts(self):
        class DummyAtomic:
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, traceback):
                return False

        class FakeCursor:
            def __init__(self):
                self.calls = []

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, traceback):
                return False

            def execute(self, sql, params=None):
                self.calls.append((sql, params or []))

        cursor = FakeCursor()
        created = MasterAuditQualifiedAuditor(
            id=UUID("11111111-1111-1111-1111-111111111111"),
            user_id="KSM0001",
            qualification_text="ISM auditor",
            qualification_date=date(2026, 8, 19),
            expiry_date=date(2028, 8, 19),
            scope_standards_csv="ISM,ISPS",
            qualifying_body="KSM Academy",
            certificate_attachment_id=UUID("22222222-2222-2222-2222-222222222222"),
            auditor_scope="INTERNAL",
            qualified_for_seq=True,
            is_active=True,
            created_by="audit-admin",
        )
        payload = {
            "user_id": "KSM0001",
            "qualification_text": "ISM auditor",
            "qualification_date": "2026-08-19",
            "expiry_date": "2028-08-19",
            "scope_standards_csv": "ISM,ISPS",
            "qualifying_body": "KSM Academy",
            "certificate_attachment_id": "22222222-2222-2222-2222-222222222222",
            "auditor_scope": "INTERNAL",
            "qualified_for_seq": True,
            "is_active": True,
        }
        request = APIRequestFactory().post("/api/audit/masters/qualified-auditors/", payload, format="json")
        user = SimpleNamespace(
            is_authenticated=True,
            id="audit-admin",
            role="SEQ_MANAGER",
            process_ids=[AUDIT_P_009],
        )
        force_authenticate(request, user=user)

        with (
            patch(
                "apps.inspection.audit.views.masters.connection",
                SimpleNamespace(vendor="microsoft", cursor=lambda: cursor),
            ),
            patch("apps.inspection.audit.views.masters.transaction.atomic", return_value=DummyAtomic()),
            patch.object(MasterAuditQualifiedAuditor.objects, "raw", return_value=[created]) as raw,
            patch(
                "apps.inspection.audit.serializers.masters.resolve_user_identity",
                return_value={
                    "name": "Capt. Harman Sandhu",
                    "designation": "SEQ Manager",
                    "company": "KSM",
                    "source": "office",
                },
            ),
        ):
            response = QualifiedAuditorListCreateView.as_view()(request)

        self.assertEqual(response.status_code, 201)
        sql, params = cursor.calls[0]
        self.assertIn("INSERT INTO dbo.master_audit_qualified_auditor", sql)
        self.assertIn("CAST(%s AS uniqueidentifier)", sql)
        self.assertEqual(params[1], "KSM0001")
        self.assertEqual(params[7], "22222222-2222-2222-2222-222222222222")
        self.assertEqual(params[11], "audit-admin")
        raw_sql, raw_params = raw.call_args.args
        self.assertIn("WHERE id = CAST(%s AS uniqueidentifier)", raw_sql)
        self.assertEqual(raw_params, [params[0]])

    def test_qualified_auditor_detail_uses_casted_uuid_lookup_on_sql_server(self):
        auditor_id = UUID("8376150e-b089-4cad-a142-34594e5d8d36")
        created = MasterAuditQualifiedAuditor(
            id=auditor_id,
            user_id="KSM0001",
            qualification_text="ISM auditor",
            qualification_date=date(2026, 8, 19),
            expiry_date=date(2028, 8, 19),
            scope_standards_csv="ISM,ISPS",
            qualifying_body="KSM Academy",
            auditor_scope="INTERNAL",
            qualified_for_seq=True,
            is_active=True,
            created_by="audit-admin",
        )

        with (
            patch("apps.inspection.audit.views.masters.connection", SimpleNamespace(vendor="microsoft")),
            patch.object(MasterAuditQualifiedAuditor.objects, "raw", return_value=[created]) as raw,
        ):
            instance = QualifiedAuditorDetailView()._get_instance(auditor_id)

        self.assertEqual(instance.id, auditor_id)
        raw_sql, raw_params = raw.call_args.args
        self.assertIn("WHERE id = CAST(%s AS uniqueidentifier)", raw_sql)
        self.assertEqual(raw_params, [str(auditor_id)])

    def test_qualified_auditor_patch_uses_casted_uuid_update_on_sql_server(self):
        class DummyAtomic:
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, traceback):
                return False

        class FakeCursor:
            def __init__(self):
                self.calls = []

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, traceback):
                return False

            def execute(self, sql, params=None):
                self.calls.append((sql, params or []))

        auditor_id = UUID("8376150e-b089-4cad-a142-34594e5d8d36")
        created = MasterAuditQualifiedAuditor(
            id=auditor_id,
            user_id="KSM0001",
            qualification_text="ISM auditor",
            qualification_date=date(2026, 8, 19),
            expiry_date=date(2028, 8, 19),
            scope_standards_csv="ISM,ISPS",
            qualifying_body="KSM Academy",
            certificate_attachment_id=UUID("22222222-2222-2222-2222-222222222222"),
            auditor_scope="INTERNAL",
            qualified_for_seq=True,
            is_active=True,
            created_by="audit-admin",
        )
        updated = MasterAuditQualifiedAuditor(
            id=auditor_id,
            user_id="KSM0001",
            qualification_text="ISM auditor - updated",
            qualification_date=date(2026, 8, 19),
            expiry_date=date(2029, 8, 19),
            scope_standards_csv="ISM,ISPS",
            qualifying_body="KSM Academy",
            certificate_attachment_id=UUID("33333333-3333-3333-3333-333333333333"),
            auditor_scope="INTERNAL",
            qualified_for_seq=True,
            is_active=True,
            created_by="audit-admin",
            updated_by="audit-admin",
        )
        payload = {
            "qualification_text": "ISM auditor - updated",
            "expiry_date": "2029-08-19",
            "certificate_attachment_id": "33333333-3333-3333-3333-333333333333",
        }
        request = APIRequestFactory().patch(
            f"/api/audit/masters/qualified-auditors/{auditor_id}/",
            payload,
            format="json",
        )
        user = SimpleNamespace(
            is_authenticated=True,
            id="audit-admin",
            role="SEQ_MANAGER",
            process_ids=[AUDIT_P_009],
        )
        force_authenticate(request, user=user)
        cursor = FakeCursor()

        with (
            patch(
                "apps.inspection.audit.views.masters.connection",
                SimpleNamespace(vendor="microsoft", cursor=lambda: cursor),
            ),
            patch("apps.inspection.audit.views.masters.transaction.atomic", return_value=DummyAtomic()),
            patch.object(MasterAuditQualifiedAuditor.objects, "raw", side_effect=[[created], [updated]]) as raw,
            patch(
                "apps.inspection.audit.serializers.masters.resolve_user_identity",
                return_value={
                    "name": "Capt. Harman Sandhu",
                    "designation": "SEQ Manager",
                    "company": "KSM",
                    "source": "office",
                },
            ),
        ):
            response = QualifiedAuditorDetailView.as_view()(request, id=auditor_id)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["data"]["qualification_text"], "ISM auditor - updated")
        update_sql, update_params = cursor.calls[0]
        self.assertIn("UPDATE dbo.master_audit_qualified_auditor", update_sql)
        self.assertIn("certificate_attachment_id = CAST(%s AS uniqueidentifier)", update_sql)
        self.assertIn("WHERE id = CAST(%s AS uniqueidentifier)", update_sql)
        self.assertEqual(update_params[2], "33333333-3333-3333-3333-333333333333")
        self.assertEqual(update_params[-3], "audit-admin")
        self.assertEqual(update_params[-1], str(auditor_id))
        self.assertEqual(raw.call_count, 2)

    def test_qualified_auditor_rejects_reversed_qualification_dates(self):
        serializer = QualifiedAuditorSerializer(
            data={
                "user_id": "KSM0001",
                "qualification_text": "ISM auditor",
                "qualification_date": date(2026, 8, 19),
                "expiry_date": date(2026, 8, 18),
                "scope_standards_csv": "ISM",
                "auditor_scope": "INTERNAL",
                "qualified_for_seq": True,
            }
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("expiry_date", serializer.errors)

    def test_acting_hod_assignment_rejects_more_than_ninety_days(self):
        serializer = HodAssignmentSerializer(
            data={
                "dept": "CREW",
                "user_id": "hod-1",
                "is_acting": True,
                "effective_from": date(2026, 8, 1),
                "effective_to": date(2026, 11, 15),
            }
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn("effective_to", serializer.errors)

    @patch("apps.inspection.audit.serializers.masters.MasterExternalAuditOrg.objects")
    def test_ro_delegation_requires_active_external_organisation(self, objects):
        objects.filter.return_value.exists.return_value = False
        serializer = VesselRoDelegationSerializer(
            data={
                "target_vessel_id": "11111111-1111-1111-1111-111111111111",
                "standard_code": "ISM",
                "master_external_audit_org_id": "22222222-2222-2222-2222-222222222222",
                "effective_from": date(2026, 8, 19),
            }
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("master_external_audit_org_id", serializer.errors)

    @patch("apps.inspection.audit.serializers.masters.MasterExternalAuditOrg.objects")
    @patch("apps.inspection.audit.serializers.masters.VesselAuditRoDelegation.objects")
    def test_ro_delegation_rejects_overlapping_window(self, delegation_objects, org_objects):
        org_objects.filter.return_value.exists.return_value = True
        delegation_objects.filter.return_value.exclude.return_value.filter.return_value.exists.return_value = True
        serializer = VesselRoDelegationSerializer(
            data={
                "target_vessel_id": "11111111-1111-1111-1111-111111111111",
                "standard_code": "ism",
                "master_external_audit_org_id": "22222222-2222-2222-2222-222222222222",
                "effective_from": date(2026, 8, 19),
                "effective_to": date(2026, 9, 19),
            }
        )
        self.assertFalse(serializer.is_valid())
        self.assertTrue(any("already covers" in str(error) for error in serializer.errors["non_field_errors"]))


if __name__ == "__main__":
    unittest.main()
