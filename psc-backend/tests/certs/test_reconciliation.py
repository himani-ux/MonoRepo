from __future__ import annotations

import os
import unittest
import uuid

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings_test")
django.setup()

from apps.certs.services.notification_dispatcher import CertNotificationRecipient
from apps.certs.services.reconciliation import (
    build_reconciliation_flags,
    dispatch_parser_anomaly_notifications,
    evaluate_reconciliation_anomalies,
    parser_anomaly_recipients,
    should_dispatch_parser_anomaly_notifications,
)


class RecordingDispatcher:
    def __init__(self) -> None:
        self.calls = []

    def dispatch(self, **kwargs):
        self.calls.append(kwargs)
        return type(
            "DispatchResult",
            (),
            {
                "notification_rows": [{"recipient_ref": recipient.user_id} for recipient in kwargs["recipients"]],
                "meta_rows": [],
                "channels_by_recipient": {recipient.user_id: recipient.channels() for recipient in kwargs["recipients"]},
            },
        )()


class CertReconciliationBucketTests(unittest.TestCase):
    def test_build_reconciliation_flags_covers_phase_4_1_buckets(self) -> None:
        catalog_match = str(uuid.uuid4())
        catalog_mismatch = str(uuid.uuid4())
        catalog_missing_class = str(uuid.uuid4())
        catalog_conditional = str(uuid.uuid4())
        catalog_extended = str(uuid.uuid4())
        tracked_match = str(uuid.uuid4())
        tracked_mismatch = str(uuid.uuid4())
        tracked_conditional = str(uuid.uuid4())
        tracked_extended = str(uuid.uuid4())

        result = build_reconciliation_flags(
            parsed_payload={
                "schema_version": 1,
                "rows": [
                    {
                        "class_code_or_name": "MATCH",
                        "certificate_number": "M-001",
                        "issue_date": "2026-01-01",
                        "expiry_date": "2031-01-01",
                        "confidence": 0.99,
                    },
                    {
                        "class_code_or_name": "MISMATCH",
                        "certificate_number": "X-NEW",
                        "issue_date": "2026-02-01",
                        "expiry_date": "2031-02-01",
                        "confidence": 0.99,
                    },
                    {
                        "class_code_or_name": "UNMAPPED",
                        "certificate_number": "U-001",
                        "confidence": 0.99,
                    },
                    {
                        "class_code_or_name": "LOWCONF",
                        "certificate_number": "L-001",
                        "confidence": 0.81,
                    },
                    {
                        "class_code_or_name": "COND",
                        "certificate_number": "C-001",
                        "validity_type": "conditional",
                        "confidence": 0.99,
                    },
                    {
                        "class_code_or_name": "EXT",
                        "certificate_number": "E-001",
                        "extension_of": "PARENT-CERT",
                        "postponed_until": "2027-01-01",
                        "confidence": 0.99,
                    },
                ],
            },
            tracked_items=[
                {
                    "tracked_item_id": tracked_match,
                    "catalog_id": catalog_match,
                    "catalog_is_class_tracked": True,
                    "certificate_number": "M-001",
                    "issue_date": "2026-01-01",
                    "expiry_date": "2031-01-01",
                },
                {
                    "tracked_item_id": tracked_mismatch,
                    "catalog_id": catalog_mismatch,
                    "catalog_is_class_tracked": True,
                    "certificate_number": "X-OLD",
                    "issue_date": "2026-02-01",
                    "expiry_date": "2030-02-01",
                },
                {
                    "tracked_item_id": str(uuid.uuid4()),
                    "catalog_id": catalog_missing_class,
                    "catalog_is_class_tracked": True,
                    "certificate_number": "ABSENT",
                    "expiry_date": "2031-03-01",
                },
                {
                    "tracked_item_id": tracked_conditional,
                    "catalog_id": catalog_conditional,
                    "catalog_is_class_tracked": True,
                    "certificate_number": "C-001",
                },
                {
                    "tracked_item_id": tracked_extended,
                    "catalog_id": catalog_extended,
                    "catalog_is_class_tracked": True,
                    "certificate_number": "E-001",
                },
            ],
            mappings=[
                {"class_code_or_name": "MATCH", "catalog_id": catalog_match, "version": 2},
                {"class_code_or_name": "MISMATCH", "catalog_id": catalog_mismatch, "version": 2},
                {"class_code_or_name": "LOWCONF", "catalog_id": str(uuid.uuid4()), "version": 2},
                {"class_code_or_name": "COND", "catalog_id": catalog_conditional, "version": 2},
                {"class_code_or_name": "EXT", "catalog_id": catalog_extended, "version": 2},
            ],
        )

        buckets = [flag["bucket"] for flag in result.flags]
        self.assertEqual(result.counts["matches_count"], 1)
        self.assertEqual(result.counts["mismatches_count"], 1)
        self.assertEqual(result.counts["missing_in_catalog_count"], 1)
        self.assertEqual(result.counts["missing_in_class_count"], 1)
        self.assertEqual(result.counts["conditional_stc_detected_count"], 1)
        self.assertEqual(result.counts["extended_postponed_detected_count"], 1)
        self.assertEqual(result.counts["unmapped_low_confidence_count"], 1)
        self.assertIn("match", buckets)
        self.assertIn("mismatch", buckets)
        self.assertIn("missing_in_catalog", buckets)
        self.assertIn("missing_in_class", buckets)
        self.assertIn("conditional_stc", buckets)
        self.assertIn("extended_postponed", buckets)
        self.assertIn("unmapped_low_confidence", buckets)

        mismatch = next(flag for flag in result.flags if flag["bucket"] == "mismatch")
        self.assertEqual(mismatch["tracked_item_id"], tracked_mismatch)
        self.assertIn("certificate_number", mismatch["diff"])
        self.assertIn("expiry_date", mismatch["diff"])
        self.assertEqual(result.anomaly_breaches, [])

    def test_evaluate_reconciliation_anomalies_records_d_cert_073_thresholds(self) -> None:
        counts = {
            "matches_count": 2,
            "mismatches_count": 2,
            "missing_in_catalog_count": 3,
            "missing_in_class_count": 0,
            "conditional_stc_detected_count": 0,
            "extended_postponed_detected_count": 0,
            "unmapped_low_confidence_count": 0,
        }

        breaches = evaluate_reconciliation_anomalies(
            counts=counts,
            parsed_payload={"rows": [{"class_code_or_name": "IOPP"}, {"class_code_or_name": "LOADLINE"}]},
            tracked_items=[
                {"catalog_is_class_tracked": True},
                {"catalog_is_class_tracked": True},
                {"catalog_is_class_tracked": True},
                {"catalog_is_class_tracked": True},
            ],
            snapshot={
                "parse_started_at": "2026-06-26T00:00:00Z",
                "parse_completed_at": "2026-06-26T00:03:01Z",
            },
        )

        by_type = {breach["type"]: breach for breach in breaches}
        self.assertEqual(by_type["mismatch_rate"]["severity"], "critical")
        self.assertEqual(by_type["mismatch_rate"]["threshold"], 0.15)
        self.assertEqual(by_type["unmapped_critical_rate"]["severity"], "critical")
        self.assertEqual(by_type["unmapped_critical_rate"]["threshold"], 0.25)
        self.assertEqual(by_type["parsed_row_count_shortfall"]["actual"], 2)
        self.assertEqual(by_type["parsed_row_count_shortfall"]["expectedClassTrackedRows"], 4)
        self.assertEqual(by_type["parse_duration"]["valueSeconds"], 181)

    def test_evaluate_reconciliation_anomalies_records_warning_for_unmapped_above_15_percent(self) -> None:
        breaches = evaluate_reconciliation_anomalies(
            counts={
                "matches_count": 4,
                "mismatches_count": 0,
                "missing_in_catalog_count": 1,
                "missing_in_class_count": 0,
                "conditional_stc_detected_count": 0,
                "extended_postponed_detected_count": 0,
                "unmapped_low_confidence_count": 0,
            },
            parsed_payload={"rows": [{"class_code_or_name": str(index)} for index in range(5)]},
            tracked_items=[{"catalog_is_class_tracked": True} for _ in range(5)],
            snapshot={"parse_started_at": "2026-06-26T00:00:00Z", "parse_completed_at": "2026-06-26T00:01:00Z"},
        )

        self.assertEqual(len(breaches), 1)
        self.assertEqual(breaches[0]["type"], "unmapped_rate")
        self.assertEqual(breaches[0]["severity"], "warning")
        self.assertEqual(breaches[0]["threshold"], 0.15)

    def test_parser_anomaly_recipients_are_office_side_by_breach_type(self) -> None:
        recipients = parser_anomaly_recipients(
            [
                {"type": "mismatch_rate", "severity": "critical"},
                {"type": "parse_duration", "severity": "critical"},
            ],
            candidates=[
                CertNotificationRecipient(user_id="dpa-1", role="DPA", side="office"),
                CertNotificationRecipient(user_id="marine-1", role="Marine Superintendent", side="office"),
                CertNotificationRecipient(user_id="tech-1", role="Technical Superintendent", side="office"),
                CertNotificationRecipient(user_id="master-1", role="Master", side="vessel"),
            ],
        )

        self.assertEqual([recipient.user_id for recipient in recipients], ["dpa-1", "marine-1", "tech-1"])
        for recipient in recipients:
            self.assertEqual(recipient.channels(), ["in_app", "slack"])

    def test_parser_anomaly_notifications_are_suppressed_for_reviewed_cutover_flags(self) -> None:
        self.assertFalse(
            should_dispatch_parser_anomaly_notifications(
                anomaly_breaches=[{"type": "unmapped_critical_rate"}],
                flags=[
                    {"bucket": "missing_in_catalog", "resolved_at": "2026-06-30T11:15:00Z"},
                    {"bucket": "mismatch", "resolved_at": "2026-06-30T11:15:00Z"},
                ],
            )
        )

    def test_parser_anomaly_notifications_dispatch_for_new_unreviewed_runs(self) -> None:
        dispatcher = RecordingDispatcher()
        result = dispatch_parser_anomaly_notifications(
            run={
                "run_id": "run-1",
                "snapshot_id": "snapshot-1",
                "vessel_id": "vessel-1",
                "vessel_name": "EAST AYUTTHAYA",
                "class_society": "KR",
                "printed_on_date": "2026-05-06",
            },
            anomaly_breaches=[{"type": "unmapped_critical_rate", "severity": "critical", "value": 0.75}],
            flags=[{"bucket": "missing_in_catalog", "resolved_at": None}],
            dispatcher=dispatcher,
            candidate_recipients=[
                CertNotificationRecipient(user_id="dpa-1", role="DPA", side="office"),
                CertNotificationRecipient(user_id="marine-1", role="Marine Superintendent", side="office"),
                CertNotificationRecipient(user_id="master-1", role="Master", side="vessel"),
            ],
        )

        self.assertEqual(result["reason"], "dispatched")
        self.assertEqual([recipient.user_id for recipient in dispatcher.calls[0]["recipients"]], ["dpa-1", "marine-1"])
        self.assertEqual(dispatcher.calls[0]["trigger_event"], "parser_anomaly")
        self.assertEqual(dispatcher.calls[0]["vessel_id"], "vessel-1")
        self.assertEqual(dispatcher.calls[0]["idempotency_scope"], "parser-anomaly:run-1")
        self.assertIn("EAST AYUTTHAYA", dispatcher.calls[0]["message"])


if __name__ == "__main__":
    unittest.main()
