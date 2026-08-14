from __future__ import annotations

import os
import unittest
import uuid
from datetime import date
from types import SimpleNamespace
from unittest.mock import patch

import django
from django.apps import apps
from django.db import connection


def bootstrap_django() -> None:
    from django.conf import settings

    os.environ.pop("DJANGO_SETTINGS_MODULE", None)
    if not settings.configured:
        settings.configure(
            SECRET_KEY="audit-certs-writeback-test-secret-key-1234567890",
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

from apps.inspection.audit.models import AuditDetail, CertWritebackOutbox  # noqa: E402
from apps.inspection.audit.services.certs_writeback import (  # noqa: E402
    drain_cert_writeback_outbox,
    enqueue_external_close_writebacks,
)


SCHEMA_MODELS = [
    AuditDetail,
    CertWritebackOutbox,
]


class FakeCertRepository:
    def __init__(self, *, applied: bool = True):
        self.applied = applied
        self.calls = []
        self.created = []

    def create_item(self, values, *, actor_id):
        self.created.append({"values": values, "actor_id": actor_id})
        return {"tracked_item_id": "created-cert-id", "version": 1}

    def apply_audit_writeback(self, tracked_item_id, values, *, actor_id, source_ref, expected_version):
        self.calls.append(
            {
                "tracked_item_id": tracked_item_id,
                "values": values,
                "actor_id": actor_id,
                "source_ref": source_ref,
                "expected_version": expected_version,
            }
        )
        before = {"tracked_item_id": tracked_item_id, "version": expected_version}
        after = {"tracked_item_id": tracked_item_id, "version": expected_version + 1}
        return before, after, self.applied


class AuditCertsWritebackTests(unittest.TestCase):
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
        self.cert_id = uuid.uuid4()
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
            linked_cert_ids_csv=str(self.cert_id),
            certificate_impact="CERT_VALID",
            created_by="auditor-1",
        )

    def test_enqueue_external_close_writeback_uses_cert_version_and_payload(self) -> None:
        with patch(
            "apps.inspection.audit.services.certs_writeback.get_cert_snapshot",
            return_value=SimpleNamespace(
                version=4,
                anniversary_date=date(2026, 7, 11),
                window_open=date(2027, 4, 11),
                window_close=date(2027, 7, 11),
                issue_date=date(2021, 7, 11),
                expiry_date=date(2026, 7, 11),
                last_done_date=date(2025, 7, 10),
                next_due_date=date(2027, 7, 11),
                status="ok",
                lifecycle_status="active",
            ),
        ):
            rows = enqueue_external_close_writebacks(
                audit_detail=self.audit_detail,
                user=SimpleNamespace(id="dpa-1"),
            )

        self.assertEqual(len(rows), 1)
        row = CertWritebackOutbox.objects.get()
        self.assertEqual(row.vessel_cert_id, self.cert_id)
        self.assertEqual(row.expected_cert_version, 4)
        self.assertEqual(row.status, "QUEUED")
        self.assertIn('"lastDoneDate": "2026-07-30"', row.writeback_payload)
        self.assertIn('"status": "ok"', row.writeback_payload)

    def test_drain_marks_sent_after_cas_writeback(self) -> None:
        CertWritebackOutbox.objects.create(
            audit_detail_id=self.audit_detail.id,
            vessel_cert_id=self.cert_id,
            writeback_payload='{"cert_update": {"lastDoneDate": "2026-07-30", "status": "ok"}}',
            expected_cert_version=4,
            status="QUEUED",
            created_by="dpa-1",
        )
        repository = FakeCertRepository(applied=True)

        result = drain_cert_writeback_outbox(repository=repository)

        row = CertWritebackOutbox.objects.get()
        self.assertEqual(result.sent, 1)
        self.assertEqual(row.status, "SENT")
        self.assertEqual(repository.calls[0]["expected_version"], 4)
        self.assertEqual(repository.calls[0]["source_ref"], f"audit_detail:{self.audit_detail.id}")

    def test_drain_marks_conflict_when_cert_version_changed(self) -> None:
        CertWritebackOutbox.objects.create(
            audit_detail_id=self.audit_detail.id,
            vessel_cert_id=self.cert_id,
            writeback_payload='{"cert_update": {"lastDoneDate": "2026-07-30", "status": "ok"}}',
            expected_cert_version=4,
            status="QUEUED",
            created_by="dpa-1",
        )

        result = drain_cert_writeback_outbox(repository=FakeCertRepository(applied=False))

        row = CertWritebackOutbox.objects.get()
        self.assertEqual(result.conflict, 1)
        self.assertEqual(row.status, "CONFLICT")
        self.assertIn("version changed", row.last_error)

    def test_initial_missing_cert_enqueues_create_and_drain_marks_sent(self) -> None:
        self.audit_detail.audit_subtype = "SMC_INITIAL"
        self.audit_detail.external_audit_subtypes_csv = "SMC_INITIAL"
        self.audit_detail.save(update_fields=["audit_subtype", "external_audit_subtypes_csv"])

        with patch("apps.inspection.audit.services.certs_writeback.get_cert_snapshot", return_value=None):
            rows = enqueue_external_close_writebacks(
                audit_detail=self.audit_detail,
                user=SimpleNamespace(id="dpa-1"),
            )

        self.assertEqual(len(rows), 1)
        row = CertWritebackOutbox.objects.get()
        self.assertEqual(row.status, "QUEUED")
        self.assertEqual(row.expected_cert_version, 0)
        self.assertIn('"operation": "CREATE_CERT"', row.writeback_payload)

        repository = FakeCertRepository()
        result = drain_cert_writeback_outbox(repository=repository)

        row.refresh_from_db()
        self.assertEqual(result.sent, 1)
        self.assertEqual(row.status, "SENT")
        self.assertEqual(repository.created[0]["values"]["anniversaryDate"], "2026-07-30")


if __name__ == "__main__":
    unittest.main()
