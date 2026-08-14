from __future__ import annotations

import os
import unittest
import uuid
from datetime import timedelta
from types import SimpleNamespace

import django
from django.apps import apps
from django.db import connection
from django.utils import timezone


def bootstrap_django() -> None:
    from django.conf import settings

    os.environ.pop("DJANGO_SETTINGS_MODULE", None)
    if not settings.configured:
        settings.configure(
            SECRET_KEY="audit-registration-test-secret-key-1234567890",
            INSTALLED_APPS=[
                "apps.accounts",
                "apps.masters",
                "apps.inspection",
                "apps.car",
                "apps.notifications",
            ],
            DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
            USE_TZ=True,
            DEFAULT_AUTO_FIELD="django.db.models.BigAutoField",
            ROOT_URLCONF="core.urls",
        )

    if not apps.ready:
        django.setup()


bootstrap_django()

from apps.accounts.models import RoleCodes  # noqa: E402
from apps.inspection.audit.models import (  # noqa: E402
    AuditAttachment,
    AuditDetail,
    AuditMeetingAttendee,
    AuditScheduleBlock,
    AuditStandard,
    AuditTeamMember,
)
from apps.inspection.audit.permissions import AUDIT_P_001, AUDIT_P_003, AUDIT_P_013  # noqa: E402
from apps.inspection.audit.views import AuditRegistrationView  # noqa: E402
from apps.inspection.models import Inspection  # noqa: E402
from rest_framework.test import APIRequestFactory, force_authenticate  # noqa: E402


SCHEMA_MODELS = [
    Inspection,
    AuditDetail,
    AuditAttachment,
    AuditStandard,
    AuditTeamMember,
    AuditMeetingAttendee,
    AuditScheduleBlock,
]


def make_user(
    *,
    role: str = RoleCodes.OFFICE_SSQE,
    user_type: str = "OFFICE",
    user_id: str = "auditor-1",
    process_ids: list[str] | None = None,
):
    return SimpleNamespace(
        id=user_id,
        role=role,
        user_type=user_type,
        process_ids=process_ids or [],
        display_name="Audit User",
        username="audit_user",
        is_authenticated=True,
    )


class AuditRegistrationApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        with connection.schema_editor() as schema_editor:
            existing_tables = set(connection.introspection.table_names())
            for model in reversed(SCHEMA_MODELS):
                if model._meta.db_table in existing_tables:
                    schema_editor.delete_model(model)
            for model in SCHEMA_MODELS:
                schema_editor.create_model(model)

    @classmethod
    def tearDownClass(cls) -> None:
        with connection.schema_editor() as schema_editor:
            for model in reversed(SCHEMA_MODELS):
                schema_editor.delete_model(model)
        super().tearDownClass()

    def setUp(self) -> None:
        with connection.cursor() as cursor:
            for model in reversed(SCHEMA_MODELS):
                cursor.execute(f"DELETE FROM {model._meta.db_table}")
        self.factory = APIRequestFactory()
        self.vessel_id = uuid.uuid4()

    def _post_registration(self, payload, user):
        request = self.factory.post("/api/audit/audits/", payload, format="json")
        force_authenticate(request, user=user)
        return AuditRegistrationView.as_view()(request)

    def _valid_payload(self):
        return {
            "vessel_id": str(self.vessel_id),
            "inspection_date": "2026-07-29",
            "port_place": "Singapore",
            "country": "Singapore",
            "inspector_name": "Lead Auditor",
            "report_reference": "F601-2026-001",
            "audit_classification": "INTERNAL",
            "auditee_type": "VESSEL",
            "audit_subtype": "ANNUAL_INTERNAL",
            "lead_auditor_name": "Lead Auditor",
            "lead_auditor_designation": "Marine Auditor",
            "lead_auditor_company": "KSM",
            "lead_auditor_qual": "ISM Lead Auditor",
            "lead_auditor_user_id": "lead-1",
            "trigger_reason": "SCHEDULED",
            "audit_start_date": "2026-07-29",
            "audit_end_date": "2026-07-30",
            "opening_meeting_at": "2026-07-29T09:00:00+05:30",
            "closing_meeting_at": "2026-07-30T16:00:00+05:30",
            "audit_scope": "Internal vessel audit scope.",
            "terms_of_reference": "SQE F 601 annual internal audit.",
            "prev_internal_ca_verified": "YES",
            "prev_external_ca_verified": "NA",
            "standards": ["ISM", "ISPS", "MLC", "EMS"],
            "team_members": [
                {
                    "member_name": "Co Auditor",
                    "member_designation": "Technical Superintendent",
                    "member_company": "KSM",
                    "member_role": "CO_AUDITOR",
                }
            ],
            "attendees": [
                {
                    "attendee_name": "Master Name",
                    "attendee_rank": "Master",
                    "opening_present": True,
                    "closing_present": True,
                }
            ],
            "schedule_blocks": [
                {
                    "block_date": "2026-07-29",
                    "time_from": "09:00:00",
                    "time_to": "10:00:00",
                    "activity": "Opening meeting",
                }
            ],
        }

    def _valid_external_payload(self):
        completed_on = timezone.localdate() - timedelta(days=10)
        return {
            "vessel_id": str(self.vessel_id),
            "inspection_date": completed_on.isoformat(),
            "port_place": "Singapore",
            "country": "Singapore",
            "authority": "DNV",
            "inspector_name": "External Surveyor",
            "report_reference": "DNV-SMC-2026-001",
            "audit_classification": "EXTERNAL",
            "auditee_type": "VESSEL",
            "audit_start_date": completed_on.isoformat(),
            "audit_end_date": completed_on.isoformat(),
            "standards": ["ISM", "ISPS", "MLC"],
            "external_audit_subtypes": ["SMC_RENEWAL", "MLC_RENEWAL", "ISPS_RENEWAL"],
            "external_audit_org_id": str(uuid.uuid4()),
            "external_audit_org_type": "CLASS_SOCIETY",
            "external_lead_auditor_name": "L. Bergstrom",
            "external_lead_auditor_credential": "IMO ISM/ISPS/MLC Auditor",
            "linked_cert_ids": [str(uuid.uuid4()), str(uuid.uuid4())],
            "external_report_file_name": "DNV-audit-report-2026.pdf",
            "external_report_file_path": "/audit/external/DNV-audit-report-2026.pdf",
            "external_report_mime_type": "application/pdf",
            "external_report_file_size": 145000,
        }

    def test_office_user_registers_internal_vessel_audit_with_f601_rows(self) -> None:
        user = make_user(process_ids=[AUDIT_P_001, AUDIT_P_003])

        response = self._post_registration(self._valid_payload(), user)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(Inspection.objects.count(), 1)
        self.assertEqual(AuditDetail.objects.count(), 1)
        inspection = Inspection.objects.get()
        audit_detail = AuditDetail.objects.get()
        self.assertEqual(inspection.inspection_type, "AUDIT")
        self.assertFalse(inspection.is_detention)
        self.assertIsNone(inspection.psc_subtype)
        self.assertEqual(audit_detail.psc_inspection_id, inspection.id.hex)
        self.assertEqual(audit_detail.vessel_id, self.vessel_id.hex)
        self.assertEqual(audit_detail.status, "IN_PROGRESS")
        self.assertEqual(set(AuditStandard.objects.values_list("standard_code", flat=True)), {"ISM", "ISPS", "MLC", "EMS"})
        self.assertEqual(AuditTeamMember.objects.get().member_role, "CO_AUDITOR")
        self.assertTrue(AuditMeetingAttendee.objects.get().opening_present)
        self.assertEqual(AuditScheduleBlock.objects.get().activity, "Opening meeting")
        self.assertEqual(response.data["data"]["inspection_id"], str(inspection.id))
        self.assertEqual(response.data["data"]["status"], "IN_PROGRESS")

    def test_vessel_user_cannot_register_audit(self) -> None:
        user = make_user(
            role=RoleCodes.VESSEL_MASTER,
            user_type="VESSEL",
            user_id="master-1",
            process_ids=[AUDIT_P_001, AUDIT_P_003],
        )

        response = self._post_registration(self._valid_payload(), user)

        self.assertEqual(response.status_code, 403)
        self.assertEqual(Inspection.objects.count(), 0)
        self.assertEqual(AuditDetail.objects.count(), 0)

    def test_office_department_requires_department_qualifier(self) -> None:
        payload = self._valid_payload()
        payload["auditee_type"] = "OFFICE_DEPT"
        payload["auditee_office_dept"] = ""
        user = make_user(process_ids=[AUDIT_P_001, AUDIT_P_003])

        response = self._post_registration(payload, user)

        self.assertEqual(response.status_code, 400)
        self.assertIn("auditee_office_dept", response.data)
        self.assertEqual(Inspection.objects.count(), 0)

    def test_registration_requires_audit_create_or_conduct_gate(self) -> None:
        user = make_user(role=RoleCodes.PHYSICAL_VERIFIER, user_id="no-gate", process_ids=[])

        response = self._post_registration(self._valid_payload(), user)

        self.assertEqual(response.status_code, 403)
        self.assertEqual(Inspection.objects.count(), 0)

    def test_master_registers_external_vessel_audit_post_facto_at_submitted(self) -> None:
        user = make_user(
            role=RoleCodes.VESSEL_MASTER,
            user_type="VESSEL",
            user_id="master-1",
            process_ids=[AUDIT_P_013],
        )

        response = self._post_registration(self._valid_external_payload(), user)

        self.assertEqual(response.status_code, 201)
        audit_detail = AuditDetail.objects.get()
        self.assertEqual(audit_detail.audit_classification, "EXTERNAL")
        self.assertEqual(audit_detail.status, "SUBMITTED")
        self.assertIsNone(audit_detail.audit_plan_id)
        self.assertEqual(audit_detail.trigger_reason, "OTHER")
        self.assertEqual(audit_detail.external_audit_subtypes_csv, "SMC_RENEWAL,MLC_RENEWAL,ISPS_RENEWAL")
        self.assertEqual(audit_detail.audit_subtype, "SMC_RENEWAL")
        self.assertEqual(audit_detail.external_audit_org_type, "CLASS_SOCIETY")
        self.assertEqual(audit_detail.external_lead_auditor_name, "L. Bergstrom")
        self.assertEqual(AuditAttachment.objects.get().category, "EXTERNAL_AUDIT_REPORT")
        self.assertEqual(response.data["data"]["status"], "SUBMITTED")

    def test_external_registration_requires_external_mandatory_fields(self) -> None:
        payload = self._valid_external_payload()
        payload["external_audit_org_id"] = None
        payload["external_report_file_name"] = ""
        user = make_user(process_ids=[AUDIT_P_013])

        response = self._post_registration(payload, user)

        self.assertEqual(response.status_code, 400)
        self.assertIn("external_audit_org_id", response.data)
        self.assertIn("external_report_file_name", response.data)
        self.assertEqual(AuditDetail.objects.count(), 0)

    def test_external_registration_over_30_days_requires_dpa_override_reason(self) -> None:
        payload = self._valid_external_payload()
        old_date = timezone.localdate() - timedelta(days=34)
        payload["inspection_date"] = old_date.isoformat()
        payload["audit_start_date"] = old_date.isoformat()
        payload["audit_end_date"] = old_date.isoformat()
        user = make_user(process_ids=[AUDIT_P_013])

        response = self._post_registration(payload, user)

        self.assertEqual(response.status_code, 400)
        self.assertIn("late_registration_reason", response.data)

        payload["late_registration_reason"] = "DPA override because the class report arrived after port departure and required office verification."
        allowed = self._post_registration(payload, user)

        self.assertEqual(allowed.status_code, 201)
        audit_detail = AuditDetail.objects.get()
        self.assertEqual(audit_detail.late_registered_by, "auditor-1")
        self.assertIsNotNone(audit_detail.late_registered_at)

    def test_doc_external_registration_requires_flag_state_and_cycle_year(self) -> None:
        payload = self._valid_external_payload()
        payload["external_audit_subtypes"] = ["DOC_RENEWAL"]
        payload["standards"] = ["DOC"]
        user = make_user(process_ids=[AUDIT_P_013])

        response = self._post_registration(payload, user)

        self.assertEqual(response.status_code, 400)
        self.assertIn("flag_state_code", response.data)
        self.assertIn("cycle_year", response.data)

    def test_duplicate_open_doc_external_audit_is_blocked_per_flag_cycle(self) -> None:
        payload = self._valid_external_payload()
        payload["external_audit_subtypes"] = ["DOC_RENEWAL"]
        payload["standards"] = ["DOC"]
        payload["flag_state_code"] = "SG"
        payload["cycle_year"] = timezone.localdate().year
        user = make_user(process_ids=[AUDIT_P_013])

        first = self._post_registration(payload, user)
        second = self._post_registration(payload, user)

        self.assertEqual(first.status_code, 201)
        self.assertEqual(second.status_code, 400)
        self.assertIn("flag_state_code", second.data)


if __name__ == "__main__":
    unittest.main()
