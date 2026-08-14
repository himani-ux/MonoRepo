from __future__ import annotations

import os
import unittest
import uuid
from datetime import date
from unittest.mock import patch

import django
from django.apps import apps
from django.db import connection
from django.utils import timezone


def bootstrap_django() -> None:
    from django.conf import settings

    os.environ.pop("DJANGO_SETTINGS_MODULE", None)
    if not settings.configured:
        settings.configure(
            SECRET_KEY="audit-finding-service-test-secret-key-1234567890",
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
        )

    if not apps.ready:
        django.setup()


bootstrap_django()

from apps.car.models import ActivityHistory  # noqa: E402
from apps.inspection.audit.models import (  # noqa: E402
    AuditDetail,
    AuditFinding,
    AuditFindingClause,
    MasterIsmClause,
)
from apps.inspection.audit.services.finding import (  # noqa: E402
    AuditFindingStateError,
    AuditFindingValidationError,
    create_audit_finding,
)
from apps.inspection.deficiency_models import CAR, Deficiency  # noqa: E402
from apps.inspection.models import Inspection  # noqa: E402


SCHEMA_MODELS = [
    Inspection,
    CAR,
    Deficiency,
    ActivityHistory,
    AuditDetail,
    AuditFinding,
    AuditFindingClause,
    MasterIsmClause,
]


class AuditFindingServiceTests(unittest.TestCase):
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
            for table_name in (
                AuditFinding._meta.db_table,
                AuditFindingClause._meta.db_table,
                MasterIsmClause._meta.db_table,
                ActivityHistory._meta.db_table,
                Deficiency._meta.db_table,
                CAR._meta.db_table,
                AuditDetail._meta.db_table,
                Inspection._meta.db_table,
            ):
                cursor.execute(f"DELETE FROM {table_name}")

        self.vessel_code_lookup = patch("apps.inspection.deficiency_models._lookup_vessel_code", return_value="TST")
        self.vessel_code_lookup.start()
        self.addCleanup(self.vessel_code_lookup.stop)

        self.vessel_id = uuid.uuid4()
        self.inspection = Inspection.objects.create(
            vessel_id=self.vessel_id,
            inspection_type="AUDIT",
            inspection_date=date(2026, 7, 29),
            port_place="Singapore",
            country="Singapore",
            created_by="auditor-1",
        )
        self.audit_detail = AuditDetail.objects.create(
            psc_inspection_id=self.inspection.id.hex,
            vessel_id=self.vessel_id.hex,
            audit_classification="INTERNAL",
            auditee_type="VESSEL",
            audit_subtype="ANNUAL_INTERNAL",
            lead_auditor_name="Lead Auditor",
            lead_auditor_company="KSM",
            trigger_reason="SCHEDULED",
            audit_start_date=date(2026, 7, 29),
            status="IN_PROGRESS",
            created_by="auditor-1",
        )
        self.ism_clause = MasterIsmClause.objects.create(
            clause_no="10.2",
            clause_text="The Company should ensure that non-conformities are reported.",
            section_no="10",
            code_version="ISM 2018",
            created_by="seed",
        )

    def test_create_nc_finding_invokes_existing_car_signal_once(self) -> None:
        result = create_audit_finding(
            audit_detail_id=self.audit_detail.id,
            finding_type="NC",
            nc_category="MINOR_NC",
            description="Fire door self-closing device was not functioning.",
            objective_evidence="Observed at deck 3 during accommodation round.",
            def_code_id="10101",
            clauses=[
                {
                    "rule_book_type": "ISM",
                    "rule_clause_id": self.ism_clause.id,
                    "is_primary": True,
                }
            ],
            created_by="auditor-1",
        )

        self.assertTrue(result.created)
        self.assertEqual(Deficiency.objects.count(), 1)
        self.assertEqual(AuditFinding.all_objects.count(), 1)
        self.assertEqual(CAR.objects.count(), 1)
        self.assertEqual(result.finding.psc_deficiency_id, result.deficiency.id.hex)
        self.assertEqual(result.deficiency.car_id, result.car.id)
        self.assertTrue(result.car.car_number.startswith(f"TST-PSC-{timezone.now().year}-"))
        self.assertEqual(result.car.status, "ALLOTTED")
        self.assertEqual(ActivityHistory.objects.filter(event_type="CAR_CREATED").count(), 1)
        self.assertEqual(AuditFindingClause.objects.count(), 1)
        self.assertEqual(result.finding.rule_book_type, "ISM")
        self.assertEqual(result.finding.rule_clause_id, self.ism_clause.id)
        self.assertEqual(result.finding.clause_ref_text, "ISM 10.2")

    def test_create_finding_persists_multi_clause_with_one_primary_mirror(self) -> None:
        result = create_audit_finding(
            audit_detail_id=self.audit_detail.id,
            finding_type="NC",
            nc_category="MAJOR_NC",
            description="Emergency generator test records did not match SMS requirement.",
            objective_evidence="Reviewed generator log and interviewed duty engineer.",
            def_code_id="10101",
            clauses=[
                {
                    "rule_book_type": "ISM",
                    "rule_clause_id": self.ism_clause.id,
                    "clause_subref_text": "10.2.1",
                    "is_primary": True,
                },
                {
                    "rule_book_type": "OTHER",
                    "clause_ref_text": "Company emergency generator test note",
                    "is_primary": False,
                },
            ],
            created_by="auditor-1",
        )

        self.assertTrue(result.created)
        self.assertEqual(AuditFindingClause.objects.count(), 2)
        primary = AuditFindingClause.objects.get(is_primary=True)
        self.assertEqual(primary.rule_book_type, "ISM")
        self.assertEqual(primary.rule_clause_id, self.ism_clause.id)
        self.assertEqual(result.finding.rule_book_type, "ISM")
        self.assertEqual(result.finding.rule_clause_id, self.ism_clause.id)
        self.assertEqual(result.finding.clause_ref_text, "ISM 10.2")

    def test_other_clause_requires_bounded_free_text(self) -> None:
        with self.assertRaises(AuditFindingValidationError):
            create_audit_finding(
                audit_detail_id=self.audit_detail.id,
                finding_type="NC",
                nc_category="MINOR_NC",
                description="Other clause text is too short.",
                objective_evidence="Observed during audit.",
                def_code_id="10101",
                clauses=[{"rule_book_type": "OTHER", "clause_ref_text": "bad", "is_primary": True}],
                created_by="auditor-1",
            )

        self.assertEqual(AuditFinding.objects.count(), 0)
        self.assertEqual(CAR.objects.count(), 0)

    def test_multi_clause_requires_exactly_one_primary(self) -> None:
        with self.assertRaises(AuditFindingValidationError):
            create_audit_finding(
                audit_detail_id=self.audit_detail.id,
                finding_type="NC",
                nc_category="MINOR_NC",
                description="Primary clause is missing.",
                objective_evidence="Observed during audit.",
                def_code_id="10101",
                clauses=[
                    {"rule_book_type": "ISM", "rule_clause_id": self.ism_clause.id, "is_primary": False},
                    {
                        "rule_book_type": "OTHER",
                        "clause_ref_text": "Company bridge checklist note",
                        "is_primary": False,
                    },
                ],
                created_by="auditor-1",
            )

        self.assertEqual(AuditFindingClause.objects.count(), 0)
        self.assertEqual(CAR.objects.count(), 0)

    def test_retry_with_same_deficiency_key_returns_existing_finding_and_car(self) -> None:
        retry_key = uuid.uuid4()
        first = create_audit_finding(
            audit_detail_id=self.audit_detail.id,
            psc_deficiency_id=retry_key,
            finding_type="OBSERVATION",
            observation_category="OFI",
            description="Bridge checklist can be made clearer for weekly review.",
            objective_evidence="Checklist wording observed during interview.",
            def_code_id="10101",
            clauses=[
                {
                    "rule_book_type": "OTHER",
                    "clause_ref_text": "Bridge checklist improvement note",
                    "is_primary": True,
                }
            ],
            created_by="auditor-1",
        )
        second = create_audit_finding(
            audit_detail_id=self.audit_detail.id,
            psc_deficiency_id=retry_key,
            finding_type="OBSERVATION",
            observation_category="OFI",
            description="Bridge checklist can be made clearer for weekly review.",
            objective_evidence="Checklist wording observed during interview.",
            def_code_id="10101",
            clauses=[
                {
                    "rule_book_type": "OTHER",
                    "clause_ref_text": "Bridge checklist improvement note",
                    "is_primary": True,
                }
            ],
            created_by="auditor-1",
        )

        self.assertTrue(first.created)
        self.assertFalse(second.created)
        self.assertEqual(first.finding.id, second.finding.id)
        self.assertEqual(first.car.id, second.car.id)
        self.assertEqual(Deficiency.objects.count(), 1)
        self.assertEqual(AuditFinding.all_objects.count(), 1)
        self.assertEqual(CAR.objects.count(), 1)

    def test_submitted_audit_rejects_new_finding_without_car_side_effect(self) -> None:
        for frozen_status in ("REPORT_FINALIZED", "VESSEL_ACKNOWLEDGED", "SUBMITTED", "DPA_CLOSED"):
            with self.subTest(frozen_status=frozen_status):
                self.audit_detail.status = frozen_status
                self.audit_detail.save(update_fields=["status"])

                with self.assertRaises(AuditFindingStateError):
                    create_audit_finding(
                        audit_detail_id=self.audit_detail.id,
                        finding_type="NC",
                        nc_category="MINOR_NC",
                        description="Late finding should not be accepted.",
                        def_code_id="10101",
                        clauses=[
                            {
                                "rule_book_type": "ISM",
                                "rule_clause_id": self.ism_clause.id,
                                "is_primary": True,
                            }
                        ],
                        created_by="auditor-1",
                    )

                self.assertEqual(Deficiency.objects.count(), 0)
                self.assertEqual(AuditFinding.all_objects.count(), 0)
                self.assertEqual(CAR.objects.count(), 0)

                self.audit_detail.status = "IN_PROGRESS"
                self.audit_detail.save(update_fields=["status"])

    def test_major_nc_certificate_impact_auto_escalates_to_critical(self) -> None:
        result = create_audit_finding(
            audit_detail_id=self.audit_detail.id,
            finding_type="NC",
            nc_category="MAJOR_NC",
            description="Certificate-threatening NC requires immediate escalation.",
            objective_evidence="External report records certificate withdrawal risk.",
            def_code_id="10101",
            priority="LOW",
            certificate_impact="SUSPENDED",
            clauses=[
                {
                    "rule_book_type": "ISM",
                    "rule_clause_id": self.ism_clause.id,
                    "is_primary": True,
                }
            ],
            created_by="auditor-1",
        )

        self.assertEqual(result.finding.priority, "CRITICAL")

    def test_non_critical_major_nc_keeps_requested_priority(self) -> None:
        result = create_audit_finding(
            audit_detail_id=self.audit_detail.id,
            finding_type="NC",
            nc_category="MAJOR_NC",
            description="Major NC without suspension impact keeps the selected priority.",
            objective_evidence="Reviewed drill records with the Master.",
            def_code_id="10101",
            priority="HIGH",
            certificate_impact="RENEWAL_AT_RISK",
            clauses=[
                {
                    "rule_book_type": "ISM",
                    "rule_clause_id": self.ism_clause.id,
                    "is_primary": True,
                }
            ],
            created_by="auditor-1",
        )

        self.assertEqual(result.finding.priority, "HIGH")

    def test_fleetwide_relevance_is_nc_only(self) -> None:
        with self.assertRaises(AuditFindingValidationError):
            create_audit_finding(
                audit_detail_id=self.audit_detail.id,
                finding_type="OBSERVATION",
                observation_category="OFI",
                description="Fleetwide observation should not be accepted.",
                objective_evidence="Interview note.",
                def_code_id="10101",
                is_fleetwide_relevance=True,
                clauses=[
                    {
                        "rule_book_type": "OTHER",
                        "clause_ref_text": "Bridge team improvement note",
                        "is_primary": True,
                    }
                ],
                created_by="auditor-1",
            )

        self.assertEqual(Deficiency.objects.count(), 0)
        self.assertEqual(AuditFinding.all_objects.count(), 0)
        self.assertEqual(CAR.objects.count(), 0)

    def test_psc_deficiency_creation_still_uses_psc_car_prefix(self) -> None:
        psc_inspection = Inspection.objects.create(
            vessel_id=self.vessel_id,
            inspection_type="PSC",
            psc_subtype="INITIAL",
            inspection_date=date(2026, 7, 29),
            port_place="Singapore",
            country="Singapore",
            created_by="psc-user",
        )

        deficiency = Deficiency.objects.create(
            inspection=psc_inspection,
            def_code_id="10101",
            def_code="10101",
            description="PSC deficiency",
            created_by="psc-user",
        )
        deficiency.refresh_from_db()

        self.assertIsNotNone(deficiency.car_id)
        self.assertTrue(deficiency.car.car_number.startswith(f"TST-PSC-{timezone.now().year}-"))


if __name__ == "__main__":
    unittest.main()
