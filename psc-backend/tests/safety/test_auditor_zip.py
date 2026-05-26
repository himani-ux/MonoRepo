from __future__ import annotations

from datetime import date, datetime, timedelta
from io import BytesIO
import os
from pathlib import Path
import shutil
from types import SimpleNamespace
import unittest
from zipfile import ZipFile

from tests.safety.support import bootstrap_django, recreate_incident_table


bootstrap_django(root_urlconf="config.urls")

from django.db import connection
from rest_framework.test import APIRequestFactory, force_authenticate

from apps.safety.models import (
    EvidenceItem,
    Incident,
    SCMAgendaItem,
    SCMAttendance,
    SCMMeeting,
    SOIFinding,
    SOIInspection,
    SOIInspectionArea,
    SOITrainee,
)
from apps.safety.views.auditor_export import AuditorBundleExportView


def build_user(*, role_name: str, user_id: str = "master-7", form_ids: list[str] | None = None) -> SimpleNamespace:
    return SimpleNamespace(
        id=user_id,
        username=user_id,
        role_name=role_name,
        form_ids=form_ids if form_ids is not None else ["SAF_F_020"],
        process_ids=[],
        vessel_ids=["7"],
        is_global=False,
    )


class AuditorZipExportTests(unittest.TestCase):
    def setUp(self) -> None:
        recreate_incident_table()
        self._recreate_step66_tables()

        self.factory = APIRequestFactory()
        self.view = AuditorBundleExportView.as_view()
        self.export_root = Path("test-output") / "auditor-zip"
        self.fixture_root = self.export_root / "fixtures"
        shutil.rmtree(self.export_root, ignore_errors=True)
        self.fixture_root.mkdir(parents=True, exist_ok=True)

        self.original_export_root = os.environ.get("SAFETY_EXPORT_ROOT")
        os.environ["SAFETY_EXPORT_ROOT"] = str(self.export_root)

        self.incident_attachment = self._write_fixture("incident/bridge-photo.jpg")
        self.near_miss_attachment = self._write_fixture("near-miss/ladder-photo.jpg")
        self.soi_attachment = self._write_fixture("soi/engine-marker.jpg")

        self._seed_incident()
        self._seed_near_miss()
        self._seed_scm()
        self._seed_soi()

    def tearDown(self) -> None:
        shutil.rmtree(self.export_root, ignore_errors=True)
        if self.original_export_root is None:
            os.environ.pop("SAFETY_EXPORT_ROOT", None)
        else:
            os.environ["SAFETY_EXPORT_ROOT"] = self.original_export_root

    def test_auditor_bundle_contains_selected_pdfs_and_attachment_subfolder(self) -> None:
        request = self.factory.post(
            "/api/safety/export/auditor-bundle/",
            {
                "record_types": ["INCIDENT", "NEAR_MISS", "SCM", "SOI"],
                "date_from": "2026-04-01",
                "date_to": "2026-04-30",
                "vessel_id": "7",
            },
            format="json",
        )
        force_authenticate(request, user=build_user(role_name="MASTER"))

        response = self.view(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/zip")
        self.assertEqual(response["X-Safety-Record-Count"], "4")
        self.assertEqual(response["X-Safety-Attachment-Count"], "3")
        self.assertIn(str(self.export_root.resolve()), response["X-Safety-Export-Path"])

        archive = ZipFile(BytesIO(response.content))
        names = archive.namelist()
        pdf_names = [name for name in names if name.lower().endswith(".pdf") and not name.startswith("attachments/")]
        attachment_names = [name for name in names if name.startswith("attachments/")]

        self.assertEqual(len(pdf_names), 4)
        self.assertEqual(len(attachment_names), 3)
        self.assertTrue(any(name.endswith("bridge-photo.jpg") for name in attachment_names))
        self.assertTrue(any(name.endswith("ladder-photo.jpg") for name in attachment_names))
        self.assertTrue(any(name.endswith("engine-marker.jpg") for name in attachment_names))

    def test_non_master_non_dpa_role_is_rejected_even_with_export_form_gate(self) -> None:
        request = self.factory.post(
            "/api/safety/export/auditor-bundle/",
            {
                "record_types": ["INCIDENT"],
                "date_from": "2026-04-01",
                "date_to": "2026-04-30",
                "vessel_id": "7",
            },
            format="json",
        )
        force_authenticate(request, user=build_user(role_name="FM", user_id="fm-1"))

        response = self.view(request)

        self.assertEqual(response.status_code, 403)

    def _write_fixture(self, relative_path: str) -> str:
        path = self.fixture_root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"fixture")
        return str(path)

    def _seed_incident(self) -> None:
        self.incident = Incident.objects.create(
            incident_number="INC/2026/041",
            vessel_id="7",
            record_type=Incident.RecordType.INCIDENT,
            state="APPROVED",
            current_phase=7,
            occurred_at=datetime.fromisoformat("2026-04-12T08:30:00+00:00"),
            reported_at=datetime.fromisoformat("2026-04-12T09:00:00+00:00"),
            narrative="Bridge access was temporarily blocked after paint drift obscured the safety marker.",
            created_by="master-7",
            updated_by="dpa-1",
            schema_version=1,
        )
        EvidenceItem.objects.create(
            incident=self.incident,
            item_type=EvidenceItem.ItemType.PHYSICAL,
            title="Bridge photo",
            description="Bridge marker photograph retained for auditor bundle coverage.",
            source_label="Photo evidence",
            metadata_json={"attachment_path": self.incident_attachment},
            created_by="master-7",
            schema_version=1,
        )

    def _seed_near_miss(self) -> None:
        self.near_miss = Incident.objects.create(
            incident_number="NM/2026/042",
            vessel_id="7",
            record_type=Incident.RecordType.NEAR_MISS,
            state="CLOSED",
            current_phase=1,
            near_miss_priority="LOW",
            occurred_at=datetime.fromisoformat("2026-04-18T05:15:00+00:00"),
            reported_at=datetime.fromisoformat("2026-04-18T05:30:00+00:00"),
            narrative="A ladder pin was found loose before use and the access point was isolated immediately.",
            reporter_id="crew-42",
            reporter_name="Crew Reporter",
            reporter_rank="AB",
            reporter_department="Deck",
            closure_reason="Immediate isolation and reset completed.",
            created_by="crew-42",
            updated_by="master-7",
            schema_version=1,
        )
        EvidenceItem.objects.create(
            incident=self.near_miss,
            item_type=EvidenceItem.ItemType.PHYSICAL,
            title="Ladder photo",
            description="Attachment for lightweight near-miss bundle coverage.",
            source_label="Near-miss photo",
            metadata_json={"photo_attachment_path": self.near_miss_attachment},
            created_by="crew-42",
            schema_version=1,
        )

    def _seed_scm(self) -> None:
        self.meeting = SCMMeeting.objects.create(
            vessel_id="7",
            scm_number="ABC-30-Apr-2026",
            meeting_type=SCMMeeting.MeetingType.REGULAR,
            meeting_date=date(2026, 4, 30) - timedelta(days=5),
            meeting_time_local="10:00:00",
            location="At Sea",
            voyage_no="VOY-600",
            chair_crew_id="master-7",
            prepared_by_crew_id="co-7",
            office_comment="Office review noted for audit completeness.",
            state=SCMMeeting.State.SIGNED_OFF,
            master_signed_off_at=datetime.fromisoformat("2026-04-25T10:45:00+00:00"),
            master_signed_off_by="master-7",
            created_by="co-7",
            updated_by="master-7",
            schema_version=1,
        )
        agenda_labels = [
            "Structured Review",
            "Outstanding Items",
            "Safety Practice",
            "Security",
            "Environment",
            "Health",
            "Crew",
            "PSC Findings & Corrective Measures",
            "Miscellaneous",
            "Office Review",
        ]
        SCMAgendaItem.objects.bulk_create(
            [
                SCMAgendaItem(
                    meeting_id=self.meeting.id,
                    agenda_item_number=index,
                    section_label=label,
                    auto_populated=False,
                    content=f"{label} notes available for the auditor ZIP bundle.",
                    decision=f"Decision recorded for {label}.",
                    schema_version=1,
                )
                for index, label in enumerate(agenda_labels, start=1)
            ]
        )
        SCMAttendance.objects.create(
            meeting_id=self.meeting.id,
            crew_id="crew-1",
            rank_name="Chief Officer",
            display_name="Chief Officer One",
            present=True,
            wrh_data_available=True,
            wrh_rest_hours_24h=10.5,
            wrh_rest_hours_7d=79.0,
            wrh_non_compliance_flag=False,
            remarks="Fit for duty.",
            schema_version=1,
        )

    def _seed_soi(self) -> None:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO master_soi_area (
                    area_id,
                    area_name,
                    section_12_flag,
                    display_order,
                    active,
                    seeded_version
                ) VALUES (%s, %s, %s, %s, %s, %s)
                """,
                [8, "Engine Control Room + Machinery Flat", False, 8, True, "v1.0"],
            )

        self.inspection = SOIInspection.objects.create(
            vessel_id="7",
            inspection_reference="SOI/ABC/26/15",
            cycle_label="Q2/2026",
            state=SOIInspection.State.REPORTED,
            planned_date=date(2026, 4, 19),
            safety_officer_crew_id="co-7",
            safety_officer_department="DECK",
            assistant_crew_id="2e-7",
            assistant_department="ENGINE",
            checklist_unique_id="SOI-UID-015",
            checklist_generated_at=datetime.fromisoformat("2026-04-18T08:00:00+00:00"),
            checklist_format=SOIInspection.ChecklistFormat.PDF,
            fieldwork_started_at=datetime.fromisoformat("2026-04-19T09:00:00+00:00"),
            reported_at=datetime.fromisoformat("2026-04-20T09:30:00+00:00"),
            created_by="co-7",
            updated_by="co-7",
            schema_version=1,
        )
        SOIInspectionArea.objects.create(
            inspection_id=self.inspection.id,
            area_id=8,
            inspected=True,
            last_inspected_at=datetime.fromisoformat("2026-04-20T09:30:00+00:00"),
            notes="Engine flat marker needs repaint.",
            schema_version=1,
        )
        SOITrainee.objects.create(
            inspection_id=self.inspection.id,
            crew_id="cadet-17",
            trainee_slot=1,
            schema_version=1,
        )
        SOIFinding.objects.create(
            inspection_id=self.inspection.id,
            area_id=8,
            item_id=8001,
            title="Engine marker faded",
            description="Engine-room emergency marker faded and no longer stands out during rounds.",
            severity="HIGH",
            priority="HIGH",
            assigned_crew_id="2e-7",
            status=SOIFinding.Status.PENDING_CLOSURE,
            photo_attachment_path=self.soi_attachment,
            created_by="co-7",
            schema_version=1,
        )

    def _recreate_step66_tables(self) -> None:
        from django.db import connection

        with connection.cursor() as cursor:
            cursor.execute("PRAGMA foreign_keys = OFF")
            cursor.execute("DROP TABLE IF EXISTS vims_safety_scm_agenda")
            cursor.execute("DROP TABLE IF EXISTS vims_safety_scm_attendance")
            cursor.execute("DROP TABLE IF EXISTS vims_safety_scm_meeting")
            cursor.execute("DROP TABLE IF EXISTS vims_safety_soi_finding")
            cursor.execute("DROP TABLE IF EXISTS vims_safety_soi_trainee")
            cursor.execute("DROP TABLE IF EXISTS vims_safety_soi_inspection_area")
            cursor.execute("DROP TABLE IF EXISTS vims_safety_soi_inspection")
            cursor.execute("DROP TABLE IF EXISTS master_soi_area")
            cursor.execute("PRAGMA foreign_keys = ON")
            cursor.execute(
                """
                CREATE TABLE master_soi_area (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    area_id INTEGER NOT NULL UNIQUE,
                    area_name VARCHAR(128) NOT NULL,
                    section_12_flag BOOLEAN NOT NULL DEFAULT 0,
                    display_order INTEGER NOT NULL,
                    active BOOLEAN NOT NULL DEFAULT 1,
                    seeded_version VARCHAR(128) NOT NULL DEFAULT 'v1.0'
                )
                """
            )

        with connection.schema_editor() as schema_editor:
            schema_editor.create_model(SCMMeeting)
            schema_editor.create_model(SCMAttendance)
            schema_editor.create_model(SCMAgendaItem)
            schema_editor.create_model(SOIInspection)
            schema_editor.create_model(SOIInspectionArea)
            schema_editor.create_model(SOITrainee)
            schema_editor.create_model(SOIFinding)
