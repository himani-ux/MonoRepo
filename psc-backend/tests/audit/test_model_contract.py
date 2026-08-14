from __future__ import annotations

import os
import unittest
import uuid

import django
from django.apps import apps
from django.db import models


def bootstrap_django() -> None:
    from django.conf import settings

    os.environ.pop("DJANGO_SETTINGS_MODULE", None)
    if not settings.configured:
        settings.configure(
            SECRET_KEY="audit-model-contract-test-secret-key-1234567890",
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

from apps.inspection.audit import models as audit_models  # noqa: E402
from apps.inspection.audit.models.base import AuditActiveManager  # noqa: E402


EXPECTED_TABLES = {
    "audit_area_summary",
    "audit_attachment",
    "audit_detail",
    "audit_finding",
    "audit_finding_clause",
    "audit_finding_nc",
    "audit_finding_obs",
    "audit_finding_sign_event",
    "audit_finding_signature",
    "audit_legacy_inspection_tag",
    "audit_meeting_attendee",
    "audit_pdf_generation",
    "audit_schedule_block",
    "audit_signature",
    "audit_standards",
    "audit_team_member",
    "cert_writeback_outbox",
    "flag_state_notification_log",
    "master_audit_area",
    "master_audit_checklist",
    "master_audit_checklist_item",
    "master_audit_classification",
    "master_audit_finding_category",
    "master_audit_plan",
    "master_audit_qualified_auditor",
    "master_audit_slack_channel",
    "master_audit_subtype",
    "master_audit_window_rule",
    "master_colreg_rule",
    "master_external_audit_org",
    "master_external_auditor",
    "master_external_auditor_category_map",
    "master_hod_assignment",
    "master_ism_clause",
    "master_isps_clause",
    "master_ksm_sms_chapter",
    "master_marpol_annex",
    "master_mlc_title",
    "master_rca_template",
    "master_solas_chapter",
    "master_stcw_section",
    "notification_delivery_log",
    "vessel_audit_ro_delegation",
}

LEGACY_CHAR32_REFERENCES = {
    audit_models.AuditDetail: {"psc_inspection_id", "parent_audit_id", "vessel_id"},
    audit_models.AuditFinding: {"psc_deficiency_id"},
    audit_models.AuditLegacyInspectionTag: {"psc_inspection_id"},
    audit_models.NotificationDeliveryLog: {"psc_notification_id"},
}

SOFT_DELETE_MODELS = {
    audit_models.AuditAttachment,
    audit_models.AuditDetail,
    audit_models.AuditFinding,
    audit_models.AuditFindingClause,
    audit_models.AuditMeetingAttendee,
    audit_models.AuditScheduleBlock,
    audit_models.AuditTeamMember,
    audit_models.MasterAuditPlan,
}


def audit_model_classes() -> list[type[models.Model]]:
    return [
        value
        for name in audit_models.__all__
        if isinstance((value := getattr(audit_models, name)), type)
        and issubclass(value, models.Model)
        and not value._meta.abstract
    ]


class AuditModelContractTests(unittest.TestCase):
    def test_exports_cover_exactly_the_43_audit_owned_tables(self) -> None:
        model_tables = {model._meta.db_table for model in audit_model_classes()}

        self.assertEqual(model_tables, EXPECTED_TABLES)
        self.assertEqual(len(model_tables), 43)
        self.assertEqual(len(audit_models.__all__), 43)

    def test_all_audit_models_use_uuid_primary_key(self) -> None:
        for model in audit_model_classes():
            with self.subTest(model=model.__name__):
                field = model._meta.get_field("id")
                self.assertIsInstance(field, models.UUIDField)
                self.assertTrue(field.primary_key)
                self.assertEqual(field.default, uuid.uuid4)

    def test_legacy_references_are_loose_char32_fields(self) -> None:
        for model, field_names in LEGACY_CHAR32_REFERENCES.items():
            for field_name in field_names:
                with self.subTest(model=model.__name__, field=field_name):
                    field = model._meta.get_field(field_name)
                    self.assertIsInstance(field, models.CharField)
                    self.assertEqual(field.max_length, 32)
                    self.assertIsNone(field.remote_field)

    def test_phase_correction_fields_are_reflected_in_models(self) -> None:
        self.assertEqual(audit_models.MasterSlackChannel._meta.db_table, "master_audit_slack_channel")
        self.assertNotIn("master_slack_channel", EXPECTED_TABLES)

        audit_detail = audit_models.AuditDetail
        self.assertIsInstance(audit_detail._meta.get_field("vessel_id"), models.CharField)
        self.assertEqual(audit_detail._meta.get_field("vessel_id").max_length, 32)
        self.assertIsInstance(audit_detail._meta.get_field("cycle_year"), models.IntegerField)

        legacy_tag = audit_models.AuditLegacyInspectionTag
        self.assertEqual(legacy_tag._meta.db_table, "audit_legacy_inspection_tag")
        self.assertTrue(legacy_tag._meta.get_field("psc_inspection_id").unique)

        checklist_item = audit_models.MasterAuditChecklistItem
        self.assertEqual(checklist_item._meta.get_field("location_code").max_length, 200)
        self.assertEqual(checklist_item._meta.get_field("regulation_ref").max_length, 500)
        self.assertEqual(audit_models.MasterStcwSection._meta.get_field("code_version").max_length, 100)

    def test_soft_delete_models_expose_filtered_and_unfiltered_managers(self) -> None:
        for model in SOFT_DELETE_MODELS:
            with self.subTest(model=model.__name__):
                self.assertIsInstance(model._default_manager, AuditActiveManager)
                self.assertIsInstance(model.objects, AuditActiveManager)
                self.assertIsInstance(model.all_objects, models.Manager)
                self.assertEqual(model.objects.model, model)
                self.assertEqual(model.all_objects.model, model)
                self.assertIn("is_deleted", str(model.objects.all().query.where))
                self.assertEqual(model.all_objects.all().query.where.children, [])


if __name__ == "__main__":
    unittest.main()
