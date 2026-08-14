from __future__ import annotations

import os
import unittest
import uuid
from datetime import date
from types import SimpleNamespace

import django
from django.apps import apps
from django.db import connection


def bootstrap_django() -> None:
    from django.conf import settings

    os.environ.pop("DJANGO_SETTINGS_MODULE", None)
    if not settings.configured:
        settings.configure(
            SECRET_KEY="audit-external-closeout-test-secret-key-1234567890",
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

from apps.inspection.audit.models import (  # noqa: E402
    AuditAttachment,
    AuditDetail,
    AuditFinding,
    AuditFindingNC,
    AuditFindingOBS,
    CertWritebackOutbox,
    FlagStateNotificationLog,
)
from apps.inspection.audit.services.external_closeout import (  # noqa: E402
    ExternalCloseoutError,
    amend_external_cert_links,
    confirm_external_audit_closeout,
)


SCHEMA_MODELS = [
    AuditDetail,
    AuditFinding,
    AuditFindingNC,
    AuditFindingOBS,
    AuditAttachment,
    CertWritebackOutbox,
    FlagStateNotificationLog,
]


class FakeCertRepository:
    def __init__(self, existing: set[str] | None = None):
        self.existing = existing or set()

    def get_item(self, tracked_item_id: str):
        if tracked_item_id not in self.existing:
            return None
        return {
            "tracked_item_id": tracked_item_id,
            "version": 3,
            "anniversary_date": date(2026, 7, 1),
            "window_open": date(2027, 4, 1),
            "window_close": date(2027, 7, 1),
            "issue_date": date(2021, 7, 1),
            "expiry_date": date(2026, 7, 1),
            "last_done_date": date(2025, 7, 1),
            "next_due_date": date(2027, 7, 1),
            "status": "ok",
            "lifecycle_status": "active",
            "certificate_number": "CERT-123",
        }


class ExternalAuditCloseoutTests(unittest.TestCase):
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
        self.user = SimpleNamespace(id="dpa-1", username="dpa", is_authenticated=True)
        self.cert_id = str(uuid.uuid4())
        self.audit_detail = AuditDetail.objects.create(
            psc_inspection_id="a" * 32,
            vessel_id="b" * 32,
            audit_classification="EXTERNAL",
            auditee_type="VESSEL",
            audit_subtype="SMC_RENEWAL",
            lead_auditor_name="External Auditor",
            lead_auditor_company="DNV",
            trigger_reason="OTHER",
            audit_start_date=date(2026, 7, 29),
            audit_end_date=date(2026, 7, 30),
            status="SUBMITTED",
            external_audit_subtypes_csv="SMC_RENEWAL",
            linked_cert_ids_csv=self.cert_id,
            created_by="auditor-1",
        )

    def _attach_closeout_letter(self) -> None:
        AuditAttachment.objects.create(
            audit_detail_id=self.audit_detail.id,
            file_name="external-closeout.pdf",
            file_path="/tmp/external-closeout.pdf",
            mime_type="application/pdf",
            category="EXTERNAL_CLOSE_OUT_LETTER",
            uploaded_by="dpa-1",
        )

    def test_internal_audit_rejects_external_certificate_impact(self) -> None:
        self.audit_detail.audit_classification = "INTERNAL"
        self.audit_detail.save(update_fields=["audit_classification"])
        self._attach_closeout_letter()

        with self.assertRaises(ExternalCloseoutError) as caught:
            confirm_external_audit_closeout(
                audit_detail=self.audit_detail,
                data={"certificate_impact": "CERT_VALID"},
                user=self.user,
            )

        self.assertEqual(caught.exception.error, "NOT_EXTERNAL_AUDIT")

    def test_closeout_requires_certificate_impact_and_letter(self) -> None:
        with self.assertRaises(ExternalCloseoutError) as no_impact:
            confirm_external_audit_closeout(audit_detail=self.audit_detail, data={}, user=self.user)
        self.assertEqual(no_impact.exception.error, "IMPACT_REQUIRED")

        with self.assertRaises(ExternalCloseoutError) as no_letter:
            confirm_external_audit_closeout(
                audit_detail=self.audit_detail,
                data={"certificate_impact": "CERT_VALID"},
                user=self.user,
            )
        self.assertEqual(no_letter.exception.error, "LETTER_REQUIRED")

    def test_suspended_closeout_requires_confirmation_and_records_flag_notification(self) -> None:
        self._attach_closeout_letter()
        major = AuditFinding.objects.create(
            audit_detail_id=self.audit_detail.id,
            psc_deficiency_id="c" * 32,
            audit_classification="EXTERNAL",
            finding_type="NC",
            nc_category="MAJOR_NC",
            is_external=True,
            created_by="auditor-1",
        )

        result = confirm_external_audit_closeout(
            audit_detail=self.audit_detail,
            data={
                "certificate_impact": "SUSPENDED",
                "typed_cert_number": "CERT-123",
                "flag_notified_to": "Flag liaison",
                "flag_notification_ref": "FLAG-2026-001",
            },
            user=self.user,
            repository=FakeCertRepository(existing={self.cert_id}),
        )

        self.audit_detail.refresh_from_db()
        self.assertEqual(self.audit_detail.certificate_impact, "SUSPENDED")
        self.assertEqual(self.audit_detail.external_closure_status, "EXTERNAL_AUDITOR_CLOSED")
        self.assertEqual(self.audit_detail.status, "DPA_CLOSED")
        self.assertEqual(FlagStateNotificationLog.objects.count(), 1)
        self.assertEqual(len(result.outbox_rows), 1)
        nc = AuditFindingNC.objects.get(audit_finding_id=major.id)
        self.assertEqual(nc.is_external_tier, "MAJOR_MANDATORY")
        self.assertEqual(nc.effectiveness_review_date, date(2026, 10, 28))

    def test_tiered_effectiveness_review_marks_minor_optional_and_observation_none(self) -> None:
        self._attach_closeout_letter()
        minor = AuditFinding.objects.create(
            audit_detail_id=self.audit_detail.id,
            psc_deficiency_id="d" * 32,
            audit_classification="EXTERNAL",
            finding_type="NC",
            nc_category="MINOR_NC",
            is_external=True,
            created_by="auditor-1",
        )
        obs = AuditFinding.objects.create(
            audit_detail_id=self.audit_detail.id,
            psc_deficiency_id="e" * 32,
            audit_classification="EXTERNAL",
            finding_type="OBSERVATION",
            observation_category="OBSERVATION",
            is_external=True,
            created_by="auditor-1",
        )
        AuditFindingOBS.objects.create(audit_finding_id=obs.id, created_by="auditor-1")

        confirm_external_audit_closeout(
            audit_detail=self.audit_detail,
            data={"certificate_impact": "CERT_VALID"},
            user=self.user,
            repository=FakeCertRepository(existing={self.cert_id}),
        )

        nc = AuditFindingNC.objects.get(audit_finding_id=minor.id)
        self.assertEqual(nc.is_external_tier, "MINOR_OPTIONAL")
        self.assertIsNone(nc.effectiveness_review_date)

    def test_initial_closeout_conflicts_when_cert_already_exists(self) -> None:
        self._attach_closeout_letter()
        self.audit_detail.audit_subtype = "SMC_INITIAL"
        self.audit_detail.external_audit_subtypes_csv = "SMC_INITIAL"
        self.audit_detail.save(update_fields=["audit_subtype", "external_audit_subtypes_csv"])

        with self.assertRaises(ExternalCloseoutError) as caught:
            confirm_external_audit_closeout(
                audit_detail=self.audit_detail,
                data={"certificate_impact": "CERT_VALID"},
                user=self.user,
                repository=FakeCertRepository(existing={self.cert_id}),
            )

        self.assertEqual(caught.exception.status_code, 409)
        self.assertEqual(caught.exception.error, "INITIAL_CERT_EXISTS")

    def test_post_closure_cert_link_edit_requires_reason_and_enqueues_outbox(self) -> None:
        self._attach_closeout_letter()
        self.audit_detail.certificate_impact = "CERT_VALID"
        self.audit_detail.external_closure_status = "EXTERNAL_AUDITOR_CLOSED"
        self.audit_detail.save(update_fields=["certificate_impact", "external_closure_status"])
        new_cert_id = str(uuid.uuid4())

        with self.assertRaises(ExternalCloseoutError) as caught:
            amend_external_cert_links(
                audit_detail=self.audit_detail,
                linked_cert_ids=[new_cert_id],
                reason="too short",
                user=self.user,
                repository=FakeCertRepository(existing={new_cert_id}),
            )
        self.assertEqual(caught.exception.error, "REASON_TOO_SHORT")

        rows = amend_external_cert_links(
            audit_detail=self.audit_detail,
            linked_cert_ids=[new_cert_id],
            reason="DPA corrected the linked certificate after reviewing the external close-out pack.",
            user=self.user,
            repository=FakeCertRepository(existing={new_cert_id}),
        )

        self.audit_detail.refresh_from_db()
        self.assertEqual(self.audit_detail.linked_cert_ids_csv, new_cert_id)
        self.assertEqual(len(rows), 1)
        self.assertEqual(CertWritebackOutbox.objects.count(), 1)


if __name__ == "__main__":
    unittest.main()
