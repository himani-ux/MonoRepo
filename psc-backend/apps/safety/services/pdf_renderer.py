from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import os
from pathlib import Path
from typing import Iterable

from django.db import connections
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from apps.safety.models import (
    CorrectiveAction,
    Incident,
    IncidentPhaseLog,
    Recommendation,
    SafetyFieldHistory,
    SCMMeeting,
    SCMSignature,
    SOIFinding,
    SOIInspection,
)
from apps.safety.repositories.scm_repo import SCMRepository
from apps.safety.repositories.soi_repo import SOIRepository
from apps.safety.serializers.scm import _blank_legacy_fields, _coerce_legacy_value, build_default_scm_sections
from apps.safety.serializers.scm_attendance import SCMAttendanceSerializer
from apps.safety.serializers.vessel_display import resolve_vessel_display
from apps.safety.repositories.reporting_repo import ReportingRepository
from apps.safety.services.closed_since_last_scm import ClosedSinceLastSCMService
from apps.safety.services.field_history_recorder import parse_history_value, resolve_actor_id, resolve_actor_role
from apps.safety.services.fleet_alert_issuer import FleetAlertIssuer
from apps.safety.services.mscmepc3_position_fetcher import Mscmepc3PositionFetcher
from apps.safety.services.pdf_post_process import PdfPostProcessor
from apps.safety.services.pdf_templates.incident_10_section import (
    IncidentPdfContext,
    IncidentPdfSignatureRow,
    IncidentTenSectionTemplate,
)
from apps.safety.services.pdf_templates.msc_mepc3_circ4 import MscMepc3Circ4PdfContext, MscMepc3Circ4Template
from apps.safety.services.pdf_templates.near_miss_lightweight import (
    NearMissLightweightPdfContext,
    NearMissLightweightTemplate,
    NearMissPdfSignatureRow,
)
from apps.safety.services.pdf_templates.scm_10_section_legacy import (
    SCMLegacyAttendanceRow,
    SCMLegacyClosedItem,
    SCMLegacyPdfContext,
    SCMLegacySectionRow,
    SCMLegacySignatureRow,
    SCMLegacySoiObservationRow,
    SCMTenSectionLegacyTemplate,
)
from apps.safety.services.pdf_templates.soi_summary import (
    SOISummaryAreaRow,
    SOISummaryFindingRow,
    SOISummaryPdfContext,
    SOISummarySignatureRow,
    SOISummaryTemplate,
    SOISummaryTraineeRow,
)
from apps.safety.services.soi_to_scm_feeder import SOIToSCMFeeder
from apps.safety.serializers.near_miss import NearMissSerializer
from apps.safety.serializers.near_miss_triage import build_near_miss_priority_hint


@dataclass(frozen=True)
class IncidentPdfRenderResult:
    content: bytes
    content_type: str
    download_path: str
    export_path: str | None
    file_name: str
    incident_id: int
    section_titles: list[str]


class IncidentPdfRenderer:
    content_type = "application/pdf"

    def __init__(
        self,
        *,
        model_class=Incident,
        template_class=IncidentTenSectionTemplate,
        post_processor_class=PdfPostProcessor,
        export_root: str | os.PathLike[str] | None = None,
    ) -> None:
        self.model_class = model_class
        self.template = template_class()
        self.post_processor = post_processor_class()
        default_root = Path.cwd() / "var" / "www" / "ksm_uploads" / "safety"
        self.export_root = Path(export_root or os.getenv("SAFETY_EXPORT_ROOT") or default_root)

    def render_incident_pdf(
        self,
        *,
        incident_id: int,
        viewer_user,
        persist: bool = True,
    ) -> IncidentPdfRenderResult:
        incident = self._get_incident(int(incident_id))
        self._validate_exportable(incident)

        context = self._build_context(incident)
        raw_content = self.template.render(context)
        final_content = self.post_processor.add_page_numbering_and_confidentiality(
            raw_content,
            incident_number=incident.incident_number,
            generated_at=context.generated_at,
        )

        export_path = None
        if persist:
            export_path = self._persist_content(incident, final_content)
            self._record_export_history(incident, export_path=export_path, user=viewer_user)

        return IncidentPdfRenderResult(
            content=final_content,
            content_type=self.content_type,
            download_path=f"/api/safety/incidents/{incident.public_id}/pdf/",
            export_path=export_path,
            file_name=self._build_file_name(incident),
            incident_id=incident.pk,
            section_titles=list(self.template.SECTION_TITLES),
        )

    def _get_incident(self, incident_id: int) -> Incident:
        return (
            self.model_class.objects.select_related("phase5_assessment")
            .prefetch_related(
                "chain_of_custody_rows",
                "cause_tags",
                "evidence_items",
                "evidence_tabs",
                "facts",
                "phase_logs",
                "recommendations__corrective_actions",
                "recommendations__verifications",
                "safeguard_failures",
                "witness_interviews",
            )
            .get(pk=incident_id, is_deleted=False)
        )

    @staticmethod
    def _validate_exportable(incident: Incident) -> None:
        if incident.record_type != Incident.RecordType.INCIDENT:
            raise ValidationError("Formal PDF export is only available for incident records.")
        if incident.current_phase < 7 and incident.state not in {"APPROVED", "CLOSED"}:
            raise ValidationError("Formal incident PDF export is available after Phase 7 acceptance.")

    def _build_context(self, incident: Incident) -> IncidentPdfContext:
        assessment = getattr(incident, "phase5_assessment", None)
        recommendations = list(incident.recommendations.filter(is_deleted=False).order_by("id"))
        return IncidentPdfContext(
            incident_id=incident.pk,
            incident_number=incident.incident_number,
            vessel_id=str(incident.vessel_id),
            current_phase=incident.current_phase,
            risk_band=incident.risk_band,
            imo_classifier=incident.imo_classifier,
            occurred_at=self._serialize_datetime(incident.occurred_at),
            reported_at=self._serialize_datetime(incident.reported_at),
            narrative=incident.narrative or "Narrative not recorded.",
            generated_at=timezone.now().isoformat(),
            cover_band_hex=self._cover_band_hex(incident.risk_band),
            investigator_rows=self._build_investigator_rows(incident),
            evidence_rows=self._build_evidence_rows(incident),
            cause_rows=self._build_cause_rows(incident),
            causal_factor_points=self._build_causal_factor_points(incident, assessment=assessment),
            action_rows=self._build_action_rows(recommendations),
            lessons_text=self._build_lessons_text(recommendations),
            notification_rows=self._build_notification_rows(incident),
            signature_rows=self._build_signature_rows(incident),
            appendix_rows=self._build_appendix_rows(incident),
            section_titles=list(self.template.SECTION_TITLES),
        )

    def _build_investigator_rows(self, incident: Incident) -> list[tuple[str, str]]:
        phase_log_roles = {(row.actor_role_code or "").upper(): row for row in incident.phase_logs.all()}
        rows = [
            ("Reporter", self._nonblank(incident.reporter_name, incident.reporter_id, default="Not recorded")),
            ("Narrative owner", self._nonblank(incident.created_by, default="Not recorded")),
            ("PIC", self._nonblank(incident.pic_user_id, default="Not assigned")),
            ("Master chain evidence", "Present" if "MASTER" in phase_log_roles else "Awaiting phase-log evidence"),
            ("HOD chain evidence", "Present" if "HOD" in phase_log_roles else "Awaiting phase-log evidence"),
            ("DPA closer", self._nonblank(incident.dpa_accepted_by, default="Awaiting closer signature")),
        ]
        if incident.risk_band == Incident.RiskBand.RED:
            rows.append(("FM approver", self._nonblank(incident.fm_approved_by, default="Awaiting FM signature")))
        return rows

    def _build_evidence_rows(self, incident: Incident) -> list[tuple[str, str, str]]:
        rows: list[tuple[str, str, str]] = []
        for tab in incident.evidence_tabs.all():
            rows.append((f"Tab {tab.tab_code}", tab.summary or "No summary recorded.", f"Entries: {tab.entry_count}"))
        for chain_row in incident.chain_of_custody_rows.all():
            rows.append(("Chain of custody", chain_row.description, chain_row.storage_location))
        for evidence_item in incident.evidence_items.all():
            rows.append((evidence_item.title, evidence_item.finding or evidence_item.description or "No detail", evidence_item.source_label or "Evidence matrix"))
        return rows or [("Evidence", "No evidence rows recorded.", "N/A")]

    def _build_cause_rows(self, incident: Incident) -> list[tuple[str, str, str]]:
        rows = [
            (cause.causal_layer.title(), cause.mscat_subcode_id, cause.rationale)
            for cause in incident.cause_tags.all().order_by("id")
        ]
        return rows or [("Root", "Uncoded", "No causal-layer rows recorded.")]

    def _build_causal_factor_points(self, incident: Incident, *, assessment) -> list[str]:
        safeguards = list(incident.safeguard_failures.all())
        evidence_titles = ", ".join(item.title for item in incident.evidence_items.all()[:3]) or "No evidence titles recorded."
        return [
            self._prefixed_point("What happened", incident.narrative or "Narrative not recorded."),
            self._prefixed_point("People", getattr(assessment, "people_contribution_text", "") or "People contribution not recorded."),
            self._prefixed_point("Process", getattr(assessment, "process_gap_text", "") or "Process gap not recorded."),
            self._prefixed_point("Plant", getattr(assessment, "plant_failure_text", "") or "Plant failure not recorded."),
            self._prefixed_point("Safeguards", safeguards[0].notes if safeguards and safeguards[0].notes else "Safeguard notes not recorded."),
            self._prefixed_point("Evidence anchors", evidence_titles),
            self._prefixed_point("Notification posture", self._notification_summary(incident)),
        ]

    def _build_action_rows(self, recommendations: Iterable[Recommendation]) -> list[tuple[str, str, str]]:
        rows: list[tuple[str, str, str]] = []
        for recommendation in recommendations:
            timeline_bits = []
            if recommendation.estimated_effort:
                timeline_bits.append(f"Effort: {recommendation.estimated_effort}")
            if recommendation.estimated_likelihood_reduction:
                timeline_bits.append(f"Likelihood reduction: {recommendation.estimated_likelihood_reduction}")
            for action in recommendation.corrective_actions.all():
                timeline_bits.append(f"CA {action.id}: {action.status}")
            for verification in recommendation.verifications.all():
                timeline_bits.append(f"Verification: {'effective' if verification.is_effective else 'pending'}")
            rows.append(
                (
                    recommendation.tier.replace("_", " ").title(),
                    recommendation.title,
                    " | ".join(timeline_bits) or "Timeline/status not recorded.",
                )
            )
        return rows or [("Lessons Learnt", "No recommendation rows recorded.", "Timeline/status not recorded.")]

    @staticmethod
    def _build_lessons_text(recommendations: Iterable[Recommendation]) -> str:
        lessons = [
            row.description.strip()
            for row in recommendations
            if row.tier == Recommendation.Tier.LESSONS_LEARNT and row.description.strip()
        ]
        if not lessons:
            return "No lessons-learnt narrative has been recorded for this incident yet."
        return " ".join(lessons)

    def _build_notification_rows(self, incident: Incident) -> list[tuple[str, str, str]]:
        rows = [
            ("DPA", "Notified" if incident.dpa_notified_at else "Pending", self._serialize_datetime(incident.dpa_notified_at) or "N/A"),
            ("FM", "Notified" if incident.fm_notified_at else "Pending", self._serialize_datetime(incident.fm_notified_at) or "N/A"),
            ("Office", "Notified" if incident.office_notified_at else "Pending", self._serialize_datetime(incident.office_notified_at) or "N/A"),
        ]
        circular_rows = SafetyFieldHistory.objects.filter(
            parent_table=incident._meta.db_table,
            parent_id=incident.pk,
            field_name="incident_circular_publish",
        ).order_by("-changed_at", "-id")
        if circular_rows.exists():
            rows.append(("Fleet Circular", "Published", self._serialize_datetime(circular_rows.first().changed_at) or "N/A"))
        return rows

    def _build_signature_rows(self, incident: Incident) -> list[IncidentPdfSignatureRow]:
        history_rows = {
            row.field_name: row
            for row in SafetyFieldHistory.objects.filter(
                parent_table=incident._meta.db_table,
                parent_id=incident.pk,
                field_name__startswith="phase7_signature_",
            )
        }
        rows = [
            self._reporter_signature_row(incident),
            self._signature_row("Master signature", row=self._role_phase_log(incident, "MASTER")),
            self._signature_row("HOD signature", row=self._role_phase_log(incident, "HOD")),
        ]
        if incident.risk_band == Incident.RiskBand.GREEN:
            rows.append(self._signature_row("PIC closer signature", row=history_rows.get("phase7_signature_pic")))
        elif incident.risk_band == Incident.RiskBand.YELLOW:
            rows.append(self._signature_row("DPA signature", row=history_rows.get("phase7_signature_dpa")))
        else:
            rows.append(self._signature_row("DPA signature", row=history_rows.get("phase7_signature_dpa")))
            rows.append(self._signature_row("FM signature", row=history_rows.get("phase7_signature_fm")))
        return rows

    def _build_appendix_rows(self, incident: Incident) -> list[tuple[str, str, str]]:
        rows: list[tuple[str, str, str]] = []
        for evidence_item in incident.evidence_items.all():
            rows.append((evidence_item.title, evidence_item.item_type, evidence_item.source_label or "Inline evidence"))
        for interview in incident.witness_interviews.all():
            rows.append((interview.witness_name, "Witness interview", interview.interview_type))
        for action in CorrectiveAction.objects.filter(source_table="vims_safety_incident", source_id=incident.pk).order_by("id"):
            rows.append((action.title, "Corrective action", action.status))
        return rows or [("Appendices", "N/A", "No appendix artifacts recorded.")]

    def _reporter_signature_row(self, incident: Incident) -> IncidentPdfSignatureRow:
        return IncidentPdfSignatureRow(
            label="Reporter signature",
            signed_by=self._nonblank(incident.reporter_id, incident.created_by, default="Awaiting signature"),
            signed_at=self._serialize_datetime(incident.reported_at) or "Awaiting signature",
            typed_name=self._nonblank(incident.reporter_name, incident.reporter_id, default="Awaiting signature"),
        )

    def _persist_content(self, incident: Incident, content: bytes) -> str:
        export_dir = self.export_root / str(incident.vessel_id) / "exports"
        export_dir.mkdir(parents=True, exist_ok=True)
        output_path = export_dir / self._build_file_name(incident)
        output_path.write_bytes(content)
        return str(output_path.resolve())

    def _record_export_history(self, incident: Incident, *, export_path: str, user) -> None:
        SafetyFieldHistory.objects.create(
            parent_table=incident._meta.db_table,
            parent_id=incident.pk,
            field_name="incident_pdf_export",
            old_value=None,
            new_value={
                "content_type": self.content_type,
                "download_path": f"/api/safety/incidents/{incident.public_id}/pdf/",
                "export_path": export_path,
                "file_name": self._build_file_name(incident),
            },
            change_reason="Formal incident PDF generated.",
            actor_user_id=resolve_actor_id(user),
            actor_role_code=resolve_actor_role(user),
            schema_version=incident.schema_version or 1,
        )

    @staticmethod
    def _build_file_name(incident: Incident) -> str:
        safe_number = "".join(char if char.isalnum() or char in {"-", "_"} else "-" for char in incident.incident_number)
        while "--" in safe_number:
            safe_number = safe_number.replace("--", "-")
        return f"{safe_number.strip('-')}-formal-report.pdf"

    @staticmethod
    def _cover_band_hex(risk_band: str | None) -> str:
        return {
            Incident.RiskBand.GREEN: "#047857",
            Incident.RiskBand.YELLOW: "#B45309",
            Incident.RiskBand.RED: "#B91C1C",
        }.get(risk_band, "#334155")

    @staticmethod
    def _serialize_datetime(value) -> str | None:
        if value is None:
            return None
        if isinstance(value, datetime):
            return value.isoformat()
        return str(value)

    @staticmethod
    def _nonblank(*values: str | None, default: str) -> str:
        for value in values:
            if value is not None and str(value).strip():
                return str(value).strip()
        return default

    @staticmethod
    def _prefixed_point(prefix: str, value: str) -> str:
        return f"{prefix}: {value.strip() if isinstance(value, str) else value}"

    def _notification_summary(self, incident: Incident) -> str:
        sent = [
            label
            for label, timestamp in (("DPA", incident.dpa_notified_at), ("FM", incident.fm_notified_at), ("Office", incident.office_notified_at))
            if timestamp
        ]
        if not sent:
            return "No notification timestamps recorded."
        return "Notifications recorded for " + ", ".join(sent) + "."

    @staticmethod
    def _role_phase_log(incident: Incident, role_code: str) -> IncidentPhaseLog | None:
        for row in incident.phase_logs.all():
            if (row.actor_role_code or "").strip().upper() == role_code:
                return row
        return None

    def _signature_row(self, label: str, *, row) -> IncidentPdfSignatureRow:
        if row is None:
            return IncidentPdfSignatureRow(label=label)
        if isinstance(row, IncidentPhaseLog):
            return IncidentPdfSignatureRow(
                label=label,
                signed_at=self._serialize_datetime(row.occurred_at),
                signed_by=row.actor_user_id,
                typed_name=row.actor_user_id,
            )

        payload = {}
        if getattr(row, "new_value", None):
            parsed = parse_history_value(row.new_value)
            if isinstance(parsed, dict):
                payload = parsed
        return IncidentPdfSignatureRow(
            label=label,
            signed_at=str(payload.get("signed_at") or self._serialize_datetime(getattr(row, "changed_at", None)) or "Awaiting signature"),
            signed_by=str(payload.get("signed_by") or getattr(row, "actor_user_id", "") or "Awaiting signature"),
            typed_name=str(payload.get("typed_name") or payload.get("signed_by") or "Awaiting signature"),
        )


@dataclass(frozen=True)
class NearMissPdfRenderResult:
    content: bytes
    content_type: str
    download_path: str
    export_path: str | None
    file_name: str
    incident_id: int
    section_titles: list[str]


class NearMissLightweightPdfRenderer:
    content_type = "application/pdf"
    _nonblank = staticmethod(IncidentPdfRenderer._nonblank)
    _serialize_datetime = staticmethod(IncidentPdfRenderer._serialize_datetime)

    def __init__(
        self,
        *,
        model_class=Incident,
        template_class=NearMissLightweightTemplate,
        post_processor_class=PdfPostProcessor,
        export_root: str | os.PathLike[str] | None = None,
    ) -> None:
        self.model_class = model_class
        self.template = template_class()
        self.post_processor = post_processor_class()
        default_root = Path.cwd() / "var" / "www" / "ksm_uploads" / "safety"
        self.export_root = Path(export_root or os.getenv("SAFETY_EXPORT_ROOT") or default_root)

    def render_near_miss_pdf(
        self,
        *,
        incident_id: int,
        viewer_user,
        persist: bool = True,
    ) -> NearMissPdfRenderResult:
        near_miss = self._get_near_miss(int(incident_id))
        self._validate_exportable(near_miss)

        context = self._build_context(near_miss, viewer_user=viewer_user)
        raw_content = self.template.render(context)
        final_content = self.post_processor.add_page_numbering_and_confidentiality(
            raw_content,
            incident_number=near_miss.incident_number,
            generated_at=context.generated_at,
        )

        export_path = None
        if persist:
            export_path = self._persist_content(near_miss, final_content)
            self._record_export_history(near_miss, export_path=export_path, user=viewer_user)

        return NearMissPdfRenderResult(
            content=final_content,
            content_type=self.content_type,
            download_path=f"/api/safety/near-miss/{near_miss.public_id}/pdf/",
            export_path=export_path,
            file_name=self._build_file_name(near_miss),
            incident_id=near_miss.pk,
            section_titles=list(self.template.SECTION_TITLES),
        )

    def _get_near_miss(self, incident_id: int) -> Incident:
        return self.model_class.objects.prefetch_related("phase_logs").get(
            pk=incident_id,
            is_deleted=False,
        )

    @staticmethod
    def _validate_exportable(near_miss: Incident) -> None:
        if near_miss.record_type != Incident.RecordType.NEAR_MISS:
            raise ValidationError("Lightweight PDF export is only available for near-miss records.")

    def _build_context(self, near_miss: Incident, *, viewer_user) -> NearMissLightweightPdfContext:
        serialized = NearMissSerializer(near_miss, context={"user": viewer_user}).data
        suggestion = build_near_miss_priority_hint(near_miss)
        viewer_visible = serialized.get("reporter_name") != "Anonymous Reporter"
        vessel_display = resolve_vessel_display(near_miss.vessel_id, user=viewer_user)
        vessel_name = vessel_display["vessel_display_name"] or str(near_miss.vessel_id)
        fleet_alert = FleetAlertIssuer()
        fleet_status = None
        fleet_learning = ""
        if near_miss.near_miss_priority == "HIGH":
            fleet_status = fleet_alert.build_status(near_miss, user=viewer_user)
            fleet_learning = fleet_alert.get_fleet_learning_text(near_miss)

        return NearMissLightweightPdfContext(
            incident_id=near_miss.pk,
            incident_number=near_miss.incident_number,
            vessel_id=vessel_name,
            state=near_miss.state or "DRAFT",
            priority=(near_miss.near_miss_priority or "UNSET").upper(),
            severity=(near_miss.near_miss_severity or "UNSET").upper(),
            occurred_at=self._serialize_datetime(near_miss.occurred_at),
            reported_at=self._serialize_datetime(near_miss.reported_at),
            reporter_name=self._nonblank(serialized.get("reporter_name"), default="Anonymous Reporter"),
            reporter_rank=self._nonblank(serialized.get("reporter_rank"), default="Masked"),
            what_happened=self._nonblank(serialized.get("narrative"), default="Narrative not recorded."),
            suggestion_text=self._build_suggestion_text(near_miss, suggestion),
            immediate_action_text=self._build_immediate_action_text(near_miss),
            closure_reason=self._nonblank(near_miss.closure_reason, default="Closure reason is not recorded."),
            fleet_alert_due_by=self._serialize_datetime(getattr(fleet_status, "due_by", None)),
            fleet_alert_issued_at=self._serialize_datetime(getattr(fleet_status, "issued_at", None)),
            fleet_alert_status=getattr(fleet_status, "sla_status", "Not required"),
            fleet_learning_text=self._nonblank(fleet_learning, default="Fleet learning / lessons are not recorded."),
            generated_at=timezone.now().isoformat(),
            visibility_note=(
                "Reporter identity is visible for DPA, FM, and the reporter. This PDF uses the same serializer masking path as the API responses."
                if viewer_visible
                else "Reporter identity is masked for this viewer per D-GAP-J1. This PDF is rendered from the masked serializer payload."
            ),
            signature_rows=self._build_signature_rows(near_miss),
        )

    @staticmethod
    def _build_immediate_action_text(near_miss: Incident) -> str:
        if (near_miss.near_miss_immediate_action or "").strip():
            return near_miss.near_miss_immediate_action.strip()
        if (near_miss.closure_reason or "").strip():
            return near_miss.closure_reason.strip()
        return "No immediate-action narrative is recorded in the current handover workspace."

    @staticmethod
    def _build_suggestion_text(near_miss: Incident, suggestion: dict[str, str]) -> str:
        if (near_miss.near_miss_suggestion or "").strip():
            return near_miss.near_miss_suggestion.strip()
        return f"Priority suggestion {suggestion['priority']}: {suggestion['rationale']}"

    def _build_signature_rows(self, near_miss: Incident) -> list[NearMissPdfSignatureRow]:
        rows: list[NearMissPdfSignatureRow] = []

        vessel_review_signature = (
            SafetyFieldHistory.objects.filter(
                parent_table=near_miss._meta.db_table,
                parent_id=near_miss.pk,
                field_name="near_miss_vessel_review_signature",
            )
            .order_by("-changed_at", "-id")
            .first()
        )
        if vessel_review_signature is not None:
            rows.append(self._field_history_signature_row("Vessel review signature", row=vessel_review_signature))

        triage_log = (
            near_miss.phase_logs.filter(actor_role_code__iexact="DPA")
            .order_by("-occurred_at", "-id")
            .first()
        )
        if triage_log is not None:
            rows.append(
                NearMissPdfSignatureRow(
                    label="Triage signature",
                    signed_at=self._serialize_datetime(triage_log.occurred_at),
                    signed_by=triage_log.actor_user_id,
                    typed_name=triage_log.actor_user_id,
                )
            )

        closure_signature = (
            SafetyFieldHistory.objects.filter(
                parent_table=near_miss._meta.db_table,
                parent_id=near_miss.pk,
                field_name="near_miss_closure_signature",
            )
            .order_by("-changed_at", "-id")
            .first()
        )
        if closure_signature is not None:
            rows.append(self._field_history_signature_row("Closure signature", row=closure_signature))
        elif near_miss.state == "CLOSED":
            rows.append(NearMissPdfSignatureRow(label="Closure signature"))
        return rows or [NearMissPdfSignatureRow(label="Triage signature")]

    def _field_history_signature_row(self, label: str, *, row) -> NearMissPdfSignatureRow:
        payload = {}
        if getattr(row, "new_value", None):
            parsed = parse_history_value(row.new_value)
            if isinstance(parsed, dict):
                payload = parsed

        return NearMissPdfSignatureRow(
            label=label,
            signed_at=str(payload.get("signed_at") or self._serialize_datetime(getattr(row, "changed_at", None)) or "Awaiting signature"),
            signed_by=str(payload.get("signed_by") or getattr(row, "actor_user_id", "") or "Awaiting signature"),
            typed_name=str(payload.get("typed_name") or payload.get("signed_by") or "Awaiting signature"),
        )

    def _persist_content(self, near_miss: Incident, content: bytes) -> str:
        export_dir = self.export_root / str(near_miss.vessel_id) / "exports"
        export_dir.mkdir(parents=True, exist_ok=True)
        output_path = export_dir / self._build_file_name(near_miss)
        output_path.write_bytes(content)
        return str(output_path.resolve())

    def _record_export_history(self, near_miss: Incident, *, export_path: str, user) -> None:
        SafetyFieldHistory.objects.create(
            parent_table=near_miss._meta.db_table,
            parent_id=near_miss.pk,
            field_name="near_miss_pdf_export",
            old_value=None,
            new_value={
                "content_type": self.content_type,
                "download_path": f"/api/safety/near-miss/{near_miss.public_id}/pdf/",
                "export_path": export_path,
                "file_name": self._build_file_name(near_miss),
            },
            change_reason="Near-miss lightweight PDF generated.",
            actor_user_id=resolve_actor_id(user),
            actor_role_code=resolve_actor_role(user),
            schema_version=near_miss.schema_version or 1,
        )

    @staticmethod
    def _build_file_name(near_miss: Incident) -> str:
        safe_number = "".join(char if char.isalnum() or char in {"-", "_"} else "-" for char in near_miss.incident_number)
        while "--" in safe_number:
            safe_number = safe_number.replace("--", "-")
        return f"{safe_number.strip('-')}-near-miss.pdf"


@dataclass(frozen=True)
class SCMPdfRenderResult:
    content: bytes
    content_type: str
    download_path: str
    export_path: str | None
    file_name: str
    meeting_id: int
    section_titles: list[str]


class SCMLegacyPdfRenderer:
    content_type = "application/pdf"
    _serialize_datetime = staticmethod(IncidentPdfRenderer._serialize_datetime)
    _nonblank = staticmethod(IncidentPdfRenderer._nonblank)

    def __init__(
        self,
        *,
        model_class=SCMMeeting,
        repository_class=SCMRepository,
        template_class=SCMTenSectionLegacyTemplate,
        post_processor_class=PdfPostProcessor,
        closed_since_service_class=ClosedSinceLastSCMService,
        soi_feed_service_class=SOIToSCMFeeder,
        export_root: str | os.PathLike[str] | None = None,
    ) -> None:
        self.model_class = model_class
        self.repository = repository_class()
        self.template = template_class()
        self.post_processor = post_processor_class()
        self.closed_since_service_class = closed_since_service_class
        self.soi_feed_service_class = soi_feed_service_class
        default_root = Path.cwd() / "var" / "www" / "ksm_uploads" / "safety"
        self.export_root = Path(export_root or os.getenv("SAFETY_EXPORT_ROOT") or default_root)

    def render_scm_pdf(
        self,
        *,
        meeting_id: int,
        viewer_user,
        persist: bool = True,
    ) -> SCMPdfRenderResult:
        meeting = self._get_meeting(int(meeting_id))
        self._validate_exportable(meeting)

        context = self._build_context(meeting)
        raw_content = self.template.render(context)
        final_content = self.post_processor.add_page_numbering_and_confidentiality(
            raw_content,
            incident_number=meeting.scm_number,
            generated_at=context.generated_at,
        )

        export_path = None
        if persist:
            export_path = self._persist_content(meeting, final_content)
            self._record_export_history(meeting, export_path=export_path, user=viewer_user)

        return SCMPdfRenderResult(
            content=final_content,
            content_type=self.content_type,
            download_path=f"/api/safety/scm/{meeting.public_id}/pdf/",
            export_path=export_path,
            file_name=self._build_file_name(meeting),
            meeting_id=meeting.pk,
            section_titles=[f"{row.agenda_item_number}. {row.section_label}" for row in context.section_rows],
        )

    def _get_meeting(self, meeting_id: int) -> SCMMeeting:
        return self.repository.read(meeting_id)

    @staticmethod
    def _validate_exportable(meeting: SCMMeeting) -> None:
        if meeting.state != SCMMeeting.State.SIGNED_OFF or meeting.master_signed_off_at is None:
            raise ValidationError("SCM PDF export is available after Master sign-off.")

    def _build_context(self, meeting: SCMMeeting) -> SCMLegacyPdfContext:
        section_rows = self._build_section_rows(meeting)
        attendance_rows = self._build_attendance_rows(meeting)
        closed_since_last = self._build_closed_since_last_payload(meeting)
        soi_auto_feed = self._build_soi_auto_feed_payload(meeting)

        return SCMLegacyPdfContext(
            meeting_id=meeting.pk,
            scm_number=meeting.scm_number,
            vessel_id=resolve_vessel_display(meeting.vessel_id)["vessel_display_name"] or str(meeting.vessel_id),
            meeting_type=meeting.meeting_type,
            meeting_date=str(meeting.meeting_date),
            meeting_time_local=str(meeting.meeting_time_local),
            occasion=str(getattr(meeting, "occasion", "") or "M"),
            ship_position=str(getattr(meeting, "ship_position", "") or "P"),
            ship_pos_from=self._nonblank(getattr(meeting, "ship_pos_from", None), default=""),
            ship_pos_to=self._nonblank(getattr(meeting, "ship_pos_to", None), default=""),
            comm_time=self._string_value(getattr(meeting, "comm_time", None)),
            comp_time=self._string_value(getattr(meeting, "comp_time", None)),
            location=self._nonblank(meeting.location, default="Not recorded"),
            latitude=self._string_value(meeting.latitude),
            longitude=self._string_value(meeting.longitude),
            voyage_no=self._nonblank(meeting.voyage_no, default="Not recorded"),
            chair_crew_id=meeting.chair_crew_id,
            prepared_by_crew_id=meeting.prepared_by_crew_id,
            state=meeting.state,
            generated_at=timezone.now().isoformat(),
            office_comment=(meeting.office_comment or "").strip() or None,
            cutoff_reference=self._build_cutoff_reference(closed_since_last.get("cutoff")),
            master_signed_off_at=self._serialize_datetime(meeting.master_signed_off_at),
            closed_since_last_counts=dict(closed_since_last.get("summary") or {}),
            closed_since_last_items=self._build_closed_item_rows(closed_since_last.get("items") or []),
            closed_since_last_empty_message=closed_since_last.get("empty_message"),
            soi_auto_feed_summary=dict(soi_auto_feed.get("section8") or {}),
            soi_observation_rows=self._build_soi_observation_rows(soi_auto_feed),
            attendance_rows=attendance_rows,
            signature_rows=self._build_signature_rows(meeting, attendance_rows=attendance_rows),
            section_rows=section_rows,
        )

    def _build_section_rows(self, meeting: SCMMeeting) -> list[SCMLegacySectionRow]:
        agenda_rows = list(self.repository.list_sections(meeting.id))
        legacy_map = self._build_legacy_field_map(meeting.id)
        if (meeting.office_comment or "").strip():
            legacy_map.setdefault(10, {})["officecomments"] = meeting.office_comment.strip()
        if getattr(meeting, "office_comment_at", None) is not None or (meeting.office_comment or "").strip():
            legacy_map.setdefault(10, {})["isreviewed"] = True
        if not agenda_rows:
            return [
                SCMLegacySectionRow(
                    agenda_item_number=int(row["agenda_item_number"]),
                    section_label=str(row["section_label"]),
                    content="No section content recorded.",
                    decision=row.get("decision"),
                    legacy_fields=_blank_legacy_fields(int(row["agenda_item_number"])),
                )
                for row in build_default_scm_sections()
            ]

        return [
            SCMLegacySectionRow(
                agenda_item_number=row.agenda_item_number,
                section_label=row.section_label,
                content=(row.content or "").strip() or "No section content recorded.",
                decision=(row.decision or "").strip() or None,
                legacy_fields={
                    **_blank_legacy_fields(int(row.agenda_item_number)),
                    **legacy_map.get(int(row.agenda_item_number), {}),
                },
            )
            for row in agenda_rows
        ]

    def _build_legacy_field_map(self, meeting_id: int) -> dict[int, dict[str, object]]:
        legacy_map: dict[int, dict[str, object]] = {}
        for field in self.repository.list_legacy_fields(meeting_id):
            legacy_map.setdefault(int(field.agenda_item_number), {})[str(field.field_key)] = _coerce_legacy_value(
                field.field_value,
                str(field.field_type),
            )
        return legacy_map

    def _build_attendance_rows(self, meeting: SCMMeeting) -> list[SCMLegacyAttendanceRow]:
        attendance = list(self.repository.list_attendance(meeting.id))
        serialized_rows = SCMAttendanceSerializer(attendance, many=True).data
        return [
            SCMLegacyAttendanceRow(
                display_name=str(row.get("display_name") or "Unknown attendee"),
                rank_name=str(row.get("rank_name") or "Unknown rank"),
                present=bool(row.get("present", True)),
                wrh_flag=str(row.get("wrh_flag") or "GREEN"),
                wrh_rest_hours_24h=self._string_value(row.get("wrh_rest_hours_24h")),
                wrh_rest_hours_7d=self._string_value(row.get("wrh_rest_hours_7d")),
                remarks=(str(row.get("remarks") or "").strip() or None),
            )
            for row in serialized_rows
        ]

    def _build_closed_since_last_payload(self, meeting: SCMMeeting) -> dict[str, object]:
        table_names = set(connections[self.model_class.objects.db].introspection.table_names())
        required_tables = {
            "vims_safety_scm_meeting",
            "vims_safety_incident",
            "vims_safety_corrective_action",
            "vims_safety_soi_finding",
            "vims_safety_soi_inspection",
        }
        if not required_tables.issubset(table_names):
            return {
                "cutoff": None,
                "summary": {
                    "incident_count": 0,
                    "near_miss_count": 0,
                    "soi_finding_count": 0,
                    "corrective_action_count": 0,
                    "total_count": 0,
                },
                "items": [],
                "empty_message": "Closed-since-last SCM data is unavailable in the current handover workspace.",
            }

        try:
            return self.closed_since_service_class().fetch_for_meeting(meeting)
        except Exception:
            return {
                "cutoff": None,
                "summary": {
                    "incident_count": 0,
                    "near_miss_count": 0,
                    "soi_finding_count": 0,
                    "corrective_action_count": 0,
                    "total_count": 0,
                },
                "items": [],
                "empty_message": "Closed-since-last SCM data could not be rendered in the current handover workspace.",
            }

    @staticmethod
    def _build_cutoff_reference(cutoff: object) -> str | None:
        if not isinstance(cutoff, dict):
            return None
        scm_number = str(cutoff.get("scm_number") or "").strip()
        closed_at = str(cutoff.get("closed_at") or "").strip()
        if scm_number and closed_at:
            return f"{scm_number} signed off at {closed_at}"
        if scm_number:
            return scm_number
        return closed_at or None

    def _build_closed_item_rows(self, items: list[dict[str, object]]) -> list[SCMLegacyClosedItem]:
        return [
            SCMLegacyClosedItem(
                item_type=str(item.get("item_type") or "ITEM"),
                reference=str(item.get("reference") or "-"),
                title=str(item.get("title") or item.get("reference") or "-"),
                status=str(item.get("status") or "-"),
                closed_at=self._string_value(item.get("closed_at")),
            )
            for item in items
        ]

    def _build_soi_auto_feed_payload(self, meeting: SCMMeeting) -> dict[str, object]:
        try:
            return self.soi_feed_service_class().fetch_for_meeting(meeting)
        except Exception:
            return {"section8": {}, "new_findings": [], "carried_forward_findings": []}

    def _build_soi_observation_rows(self, payload: dict[str, object]) -> list[SCMLegacySoiObservationRow]:
        rows: list[SCMLegacySoiObservationRow] = []
        for row in list(payload.get("new_findings") or []) + list(payload.get("carried_forward_findings") or []):
            if not isinstance(row, dict):
                continue
            rows.append(
                SCMLegacySoiObservationRow(
                    reference=str(row.get("inspection_reference") or row.get("finding_id") or "-"),
                    title=str(row.get("title") or row.get("description") or "SOI finding"),
                    severity=str(row.get("severity") or "-"),
                    status=str(row.get("status") or "-"),
                    corrective_measure=self._string_value(row.get("proposed_action")),
                    carried_forward_count=int(row.get("carried_forward_count") or 0),
                )
            )
        return rows

    def _build_signature_rows(
        self,
        meeting: SCMMeeting,
        *,
        attendance_rows: list[SCMLegacyAttendanceRow],
    ) -> list[SCMLegacySignatureRow]:
        rows: list[SCMLegacySignatureRow] = []
        signature_rows = list(
            SCMSignature.objects.filter(meeting_id=meeting.id).order_by("signer_role", "signed_at", "id")
        )
        if signature_rows:
            role_labels = {
                SCMSignature.SignerRole.MASTER: "Master signature",
                SCMSignature.SignerRole.CO: "CO co-signature",
                SCMSignature.SignerRole.ATTENDEE: "Attendee signature",
            }
            return [
                SCMLegacySignatureRow(
                    label=(
                        f"Attendee - {row.display_name}"
                        if row.signer_role == SCMSignature.SignerRole.ATTENDEE
                        else role_labels.get(row.signer_role, row.signer_role)
                    ),
                    status="Signed",
                    signed_by=row.signer_crew_id,
                    signed_at=self._serialize_datetime(row.signed_at),
                    typed_name=row.typed_name,
                    note=f"Device fingerprint: {row.device_fingerprint}",
                )
                for row in signature_rows
            ]
        master_signature = (
            SafetyFieldHistory.objects.filter(
                parent_table=meeting._meta.db_table,
                parent_id=meeting.pk,
                field_name="scm_signoff_signature",
            )
            .order_by("-changed_at", "-id")
            .first()
        )
        if master_signature is not None:
            rows.append(self._field_history_signature_row("Master signature", row=master_signature))
        else:
            rows.append(
                SCMLegacySignatureRow(
                    label="Master signature",
                    status="Awaiting signature",
                    note="Master hybrid digital signature has not been recorded yet.",
                )
            )

        if meeting.meeting_type == SCMMeeting.MeetingType.REGULAR:
            rows.append(
                SCMLegacySignatureRow(
                    label="CO co-signature",
                    status="Not captured",
                    signed_by=meeting.prepared_by_crew_id,
                    typed_name=meeting.prepared_by_crew_id,
                    note="CO digital signature is not captured for this historical SCM record.",
                )
            )
        else:
            rows.append(
                SCMLegacySignatureRow(
                    label="Ad-Hoc preparer",
                    status="Captured via Master sign-off",
                    signed_by=meeting.prepared_by_crew_id,
                    typed_name=meeting.prepared_by_crew_id,
                    note="Ad-Hoc SCM is prepared and signed by the Master in the current contract.",
                )
            )

        for attendee in attendance_rows:
            rows.append(
                SCMLegacySignatureRow(
                    label=f"Attendee - {attendee.display_name}",
                    status="Attendance recorded" if attendee.present else "Absent",
                    signed_by=attendee.display_name,
                    typed_name=attendee.display_name if attendee.present else None,
                    note=(
                        "Attendance is persisted, but attendee digital signature was not captured for this historical SCM record."
                        if attendee.present
                        else "Absent attendee; no digital signature recorded."
                    ),
                )
            )
        return rows

    def _field_history_signature_row(self, label: str, *, row) -> SCMLegacySignatureRow:
        payload = {}
        if getattr(row, "new_value", None):
            parsed = parse_history_value(row.new_value)
            if isinstance(parsed, dict):
                payload = parsed
        return SCMLegacySignatureRow(
            label=label,
            status="Signed",
            signed_by=str(payload.get("signed_by") or getattr(row, "actor_user_id", "") or "-"),
            signed_at=str(payload.get("signed_at") or self._serialize_datetime(getattr(row, "changed_at", None)) or "-"),
            typed_name=str(payload.get("typed_name") or payload.get("signed_by") or "-"),
            note=f"Device fingerprint: {payload.get('device_fingerprint')}" if payload.get("device_fingerprint") else None,
        )

    def _persist_content(self, meeting: SCMMeeting, content: bytes) -> str:
        export_dir = self.export_root / str(meeting.vessel_id) / "exports"
        export_dir.mkdir(parents=True, exist_ok=True)
        output_path = export_dir / self._build_file_name(meeting)
        output_path.write_bytes(content)
        meeting.pdf_export_path = str(output_path.resolve())
        meeting.save(update_fields=["pdf_export_path"])
        return str(output_path.resolve())

    def _record_export_history(self, meeting: SCMMeeting, *, export_path: str, user) -> None:
        SafetyFieldHistory.objects.create(
            parent_table=meeting._meta.db_table,
            parent_id=meeting.pk,
            field_name="scm_pdf_export",
            old_value=None,
            new_value={
                "content_type": self.content_type,
                "download_path": f"/api/safety/scm/{meeting.public_id}/pdf/",
                "export_path": export_path,
                "file_name": self._build_file_name(meeting),
            },
            change_reason="SCM legacy PDF generated.",
            actor_user_id=resolve_actor_id(user),
            actor_role_code=resolve_actor_role(user),
            schema_version=meeting.schema_version or 1,
        )

    @staticmethod
    def _build_file_name(meeting: SCMMeeting) -> str:
        safe_number = "".join(char if char.isalnum() or char in {"-", "_"} else "-" for char in meeting.scm_number)
        while "--" in safe_number:
            safe_number = safe_number.replace("--", "-")
        return f"{safe_number.strip('-')}-scm-legacy.pdf"

    @staticmethod
    def _string_value(value) -> str:
        if value in (None, ""):
            return "-"
        return str(value)


@dataclass(frozen=True)
class SOISummaryPdfRenderResult:
    content: bytes
    content_type: str
    download_path: str
    export_path: str | None
    file_name: str
    inspection_id: int
    section_titles: list[str]


class SOISummaryPdfRenderer:
    content_type = "application/pdf"
    _serialize_datetime = staticmethod(IncidentPdfRenderer._serialize_datetime)
    _nonblank = staticmethod(IncidentPdfRenderer._nonblank)

    def __init__(
        self,
        *,
        model_class=SOIInspection,
        finding_model=SOIFinding,
        repository_class=SOIRepository,
        template_class=SOISummaryTemplate,
        post_processor_class=PdfPostProcessor,
        export_root: str | os.PathLike[str] | None = None,
    ) -> None:
        self.model_class = model_class
        self.finding_model = finding_model
        self.repository = repository_class()
        self.template = template_class()
        self.post_processor = post_processor_class()
        default_root = Path.cwd() / "var" / "www" / "ksm_uploads" / "safety"
        self.export_root = Path(export_root or os.getenv("SAFETY_EXPORT_ROOT") or default_root)

    def render_soi_pdf(
        self,
        *,
        inspection_id: int,
        viewer_user,
        persist: bool = True,
    ) -> SOISummaryPdfRenderResult:
        inspection = self._get_inspection(int(inspection_id))
        self._validate_exportable(inspection)

        context = self._build_context(inspection)
        raw_content = self.template.render(context)
        final_content = self.post_processor.add_page_numbering_and_confidentiality(
            raw_content,
            incident_number=inspection.inspection_reference,
            generated_at=context.generated_at,
        )

        export_path = None
        if persist:
            export_path = self._persist_content(inspection, final_content)
            self._record_export_history(inspection, export_path=export_path, user=viewer_user)

        return SOISummaryPdfRenderResult(
            content=final_content,
            content_type=self.content_type,
            download_path=f"/api/safety/soi/{inspection.public_id}/pdf/",
            export_path=export_path,
            file_name=self._build_file_name(inspection),
            inspection_id=inspection.pk,
            section_titles=list(self.template.SECTION_TITLES),
        )

    def _get_inspection(self, inspection_id: int) -> SOIInspection:
        return self.model_class.objects.get(pk=inspection_id, is_deleted=False)

    @staticmethod
    def _validate_exportable(inspection: SOIInspection) -> None:
        if inspection.state not in {SOIInspection.State.REPORTED, SOIInspection.State.CLOSED}:
            raise ValidationError("SOI summary PDF export is available after inspection submission.")
        if inspection.reported_at is None:
            raise ValidationError("SOI summary PDF export requires a reported_at timestamp.")
        if not inspection.checklist_unique_id:
            raise ValidationError("SOI summary PDF export requires a checklist unique ID.")

    def _build_context(self, inspection: SOIInspection) -> SOISummaryPdfContext:
        selected_areas = self.repository.list_selected_areas(inspection.id)
        trainees = self.repository.list_trainees(inspection.id)
        findings = list(
            self.finding_model.objects.filter(inspection_id=inspection.id, is_deleted=False).order_by("area_id", "id")
        )

        return SOISummaryPdfContext(
            inspection_id=inspection.pk,
            inspection_reference=inspection.inspection_reference,
            vessel_id=str(inspection.vessel_id),
            cycle_label=inspection.cycle_label,
            state=inspection.state,
            planned_date=str(inspection.planned_date),
            reported_at=self._serialize_datetime(inspection.reported_at),
            closed_at=self._serialize_datetime(inspection.closed_at),
            checklist_unique_id=str(inspection.checklist_unique_id),
            generated_at=timezone.now().isoformat(),
            scm_feed_indicator=(
                "Included in the Closed-Since-Last SCM feed now that the inspection is reported."
            ),
            paper_reference_note=(
                f"Paper checklist: unique-ID {inspection.checklist_unique_id}, filed in ship SMS filing system."
            ),
            audit_footer=(
                f"Audit trail: record ID {inspection.pk} | schema version {inspection.schema_version} | "
                f"planned {inspection.planned_date} | reported {self._serialize_datetime(inspection.reported_at) or 'N/A'} | "
                f"closed {self._serialize_datetime(inspection.closed_at) or 'Awaiting Master closure'}"
            ),
            area_rows=self._build_area_rows(selected_areas),
            finding_rows=self._build_finding_rows(findings),
            trainee_rows=self._build_trainee_rows(trainees),
            signature_rows=self._build_signature_rows(inspection),
        )

    @staticmethod
    def _build_area_rows(rows: list[dict[str, object]]) -> list[SOISummaryAreaRow]:
        return [
            SOISummaryAreaRow(
                area_id=int(row["area_id"]),
                area_name=str(row["area_name"]),
                last_inspected_at=IncidentPdfRenderer._serialize_datetime(row.get("last_inspected_at")),
                status="Stamped" if bool(row.get("inspected")) else "Pending",
            )
            for row in rows
        ]

    def _build_finding_rows(self, findings: list[SOIFinding]) -> list[SOISummaryFindingRow]:
        return [
            SOISummaryFindingRow(
                title=self._nonblank(finding.title, default="Untitled finding"),
                severity=finding.severity,
                mscat_code=self._nonblank(finding.mscat_subcode_id, default="-"),
                shell_tag=self._nonblank(finding.shell_tag, default="-"),
                priority=finding.priority,
                assignee=self._nonblank(finding.assigned_crew_id, default="Unassigned"),
                status=finding.status,
            )
            for finding in findings
        ]

    @staticmethod
    def _build_trainee_rows(rows: list[dict[str, object]]) -> list[SOISummaryTraineeRow]:
        return [
            SOISummaryTraineeRow(
                crew_id=str(row["crew_id"]),
                trainee_slot=int(row["trainee_slot"]),
            )
            for row in rows
        ]

    def _build_signature_rows(self, inspection: SOIInspection) -> list[SOISummarySignatureRow]:
        rows = [
            SOISummarySignatureRow(
                label="Safety Officer paper signature",
                status="Paper sign-off on filed checklist",
                signed_by=inspection.safety_officer_crew_id,
                note="Paper signature remains on the filed checklist; no separate digital event-signature row exists in the current workspace.",
            ),
            SOISummarySignatureRow(
                label="Assistant paper signature",
                status="Paper sign-off on filed checklist",
                signed_by=inspection.assistant_crew_id,
                note="Paper signature remains on the filed checklist; no separate digital event-signature row exists in the current workspace.",
            ),
        ]

        master_signature = (
            SafetyFieldHistory.objects.filter(
                parent_table=inspection._meta.db_table,
                parent_id=inspection.pk,
                field_name="soi_close_signature",
            )
            .order_by("-changed_at", "-id")
            .first()
        )
        if master_signature is None:
            rows.append(
                SOISummarySignatureRow(
                    label="Master digital approval",
                    status="Awaiting Master closure",
                    signed_by=inspection.master_crew_id,
                    note="The Master digital counter-signature is captured when the SOI event is closed.",
                )
            )
            return rows

        payload = {}
        if getattr(master_signature, "new_value", None):
            parsed = parse_history_value(master_signature.new_value)
            if isinstance(parsed, dict):
                payload = parsed
        rows.append(
            SOISummarySignatureRow(
                label="Master digital approval",
                status="Signed",
                signed_by=str(payload.get("typed_name") or payload.get("signed_by") or inspection.master_crew_id or "-"),
                signed_at=str(
                    payload.get("signed_at")
                    or self._serialize_datetime(getattr(master_signature, "changed_at", None))
                    or "-"
                ),
                note=(
                    f"Device fingerprint: {payload.get('device_fingerprint')}"
                    if payload.get("device_fingerprint")
                    else None
                ),
            )
        )
        return rows

    def _persist_content(self, inspection: SOIInspection, content: bytes) -> str:
        export_dir = self.export_root / str(inspection.vessel_id) / "exports"
        export_dir.mkdir(parents=True, exist_ok=True)
        output_path = export_dir / self._build_file_name(inspection)
        output_path.write_bytes(content)
        return str(output_path.resolve())

    def _record_export_history(self, inspection: SOIInspection, *, export_path: str, user) -> None:
        SafetyFieldHistory.objects.create(
            parent_table=inspection._meta.db_table,
            parent_id=inspection.pk,
            field_name="soi_summary_pdf_export",
            old_value=None,
            new_value={
                "content_type": self.content_type,
                "download_path": f"/api/safety/soi/{inspection.public_id}/pdf/",
                "export_path": export_path,
                "file_name": self._build_file_name(inspection),
            },
            change_reason="SOI summary PDF generated.",
            actor_user_id=resolve_actor_id(user),
            actor_role_code=resolve_actor_role(user),
            schema_version=inspection.schema_version or 1,
        )

    @staticmethod
    def _build_file_name(inspection: SOIInspection) -> str:
        safe_reference = "".join(
            char if char.isalnum() or char in {"-", "_"} else "-"
            for char in inspection.inspection_reference
        )
        while "--" in safe_reference:
            safe_reference = safe_reference.replace("--", "-")
        return f"{safe_reference.strip('-')}-soi-summary.pdf"


@dataclass(frozen=True)
class MscMepc3PdfRenderResult:
    content: bytes
    content_type: str
    download_path: str
    export_path: str | None
    file_name: str
    incident_id: int
    appendix_titles: list[str]


class MscMepc3Circ4PdfRenderer:
    content_type = "application/pdf"
    _nonblank = staticmethod(IncidentPdfRenderer._nonblank)
    _serialize_datetime = staticmethod(IncidentPdfRenderer._serialize_datetime)
    _report_column_map = {
        "NoonReport": {
            "lat_columns": ("Lattitude1", "Lattitude2", "Lattitude3"),
            "lon_columns": ("Longitude1", "Longitud2", "Longitud3"),
        },
        "DepartureReport": {
            "lat_columns": ("Lattitude1", "Lattitude2", "Lattitude3"),
            "lon_columns": ("Longitude1", "Longitude2", "Longitude3"),
        },
        "ArrivalReport": {
            "lat_columns": ("Lattitude1", "Lattitude2", "Lattitude3"),
            "lon_columns": ("Longitude1", "Longitud2", "Longitud3"),
        },
        "NoonReportPort": {
            "lat_columns": ("Latitude1", "Latitude2", "Latitude3"),
            "lon_columns": ("Longitude1", "Longitude2", "Longitude3"),
        },
    }

    def __init__(
        self,
        *,
        model_class=Incident,
        template_class=MscMepc3Circ4Template,
        post_processor_class=PdfPostProcessor,
        position_fetcher_class=Mscmepc3PositionFetcher,
        reporting_repository_class=ReportingRepository,
        export_root: str | os.PathLike[str] | None = None,
    ) -> None:
        self.model_class = model_class
        self.template = template_class()
        self.post_processor = post_processor_class()
        self.position_fetcher = position_fetcher_class(reporting_repository=reporting_repository_class())
        default_root = Path.cwd() / "var" / "www" / "ksm_uploads" / "safety"
        self.export_root = Path(export_root or os.getenv("SAFETY_EXPORT_ROOT") or default_root)

    def render_export_pdf(
        self,
        *,
        incident_id: int,
        viewer_user,
        persist: bool = True,
    ) -> MscMepc3PdfRenderResult:
        incident = self._get_incident(int(incident_id))
        self._validate_exportable(incident)

        context = self._build_context(incident)
        raw_content = self.template.render(context)
        final_content = self.post_processor.add_page_numbering_and_confidentiality(
            raw_content,
            incident_number=incident.incident_number,
            generated_at=context.generated_at,
        )

        export_path = None
        if persist:
            export_path = self._persist_content(incident, final_content)
            self._record_export_history(incident, export_path=export_path, user=viewer_user)

        return MscMepc3PdfRenderResult(
            content=final_content,
            content_type=self.content_type,
            download_path=f"/api/safety/export/msc-mepc-3/{incident.public_id}/",
            export_path=export_path,
            file_name=self._build_file_name(incident),
            incident_id=incident.pk,
            appendix_titles=list(self.template.APPENDIX_TITLES),
        )

    def _get_incident(self, incident_id: int) -> Incident:
        return (
            self.model_class.objects.prefetch_related(
                "cause_tags",
                "facts",
                "recommendations__corrective_actions",
            )
            .get(pk=incident_id, is_deleted=False)
        )

    @staticmethod
    def _validate_exportable(incident: Incident) -> None:
        if incident.record_type != Incident.RecordType.INCIDENT:
            raise ValidationError("MSC-MEPC.3/Circ.4 export is only available for incident records.")
        if incident.current_phase < 7 and incident.state not in {"APPROVED", "CLOSED"}:
            raise ValidationError("MSC-MEPC.3/Circ.4 export is available after Phase 7 acceptance.")
        if incident.imo_classifier not in {
            Incident.ImoClassifier.SMC,
            Incident.ImoClassifier.MC,
            Incident.ImoClassifier.MI,
        }:
            raise ValidationError(
                "MSC-MEPC.3/Circ.4 export requires an applicable IMO classifier: SMC, MC, or MI."
            )

    def _build_context(self, incident: Incident) -> MscMepc3Circ4PdfContext:
        vessel_particulars = self._load_vessel_particulars(incident)
        reporting_context = self._load_reporting_context(incident, vessel_particulars=vessel_particulars)
        return MscMepc3Circ4PdfContext(
            incident_id=incident.pk,
            incident_number=incident.incident_number,
            generated_at=timezone.now().isoformat(),
            appendix_titles=list(self.template.APPENDIX_TITLES),
            appendix1_rows=self._build_appendix1_rows(incident, reporting_context=reporting_context),
            appendix2_rows=self._build_appendix2_rows(vessel_particulars, reporting_context=reporting_context),
            appendix3_rows=self._build_appendix3_rows(incident),
            appendix4_rows=self._build_appendix4_rows(incident, reporting_context=reporting_context),
            appendix5_rows=self._build_appendix5_rows(
                incident,
                vessel_particulars=vessel_particulars,
                reporting_context=reporting_context,
            ),
        )

    def _build_appendix1_rows(
        self,
        incident: Incident,
        *,
        reporting_context: dict[str, object],
    ) -> list[tuple[str, str]]:
        reporter = self._nonblank(incident.reporter_name, incident.reporter_id, default="Not recorded")
        investigating_authority = self._nonblank(
            incident.fm_approved_by,
            incident.dpa_accepted_by,
            default="DPA review pending",
        )
        position_reference = self._nonblank(
            str(reporting_context.get("source_reference") or ""),
            incident.position_daily_report_id,
            default="Manual position / no Daily Report match",
        )
        return [
            ("Incident reference", incident.incident_number),
            ("Occurred at", self._serialize_datetime(incident.occurred_at) or "Not recorded"),
            ("Reported at", self._serialize_datetime(incident.reported_at) or "Not recorded"),
            ("Reporter", reporter),
            ("Reporter rank", self._nonblank(incident.reporter_rank, default="Not recorded")),
            ("Investigating authority", investigating_authority),
            ("Current phase", str(incident.current_phase)),
            ("Risk band", incident.risk_band or "Unassigned"),
            ("IMO classifier", incident.imo_classifier or "Not assigned"),
            ("Position source reference", position_reference),
        ]

    def _build_appendix2_rows(
        self,
        vessel_particulars: dict[str, object],
        *,
        reporting_context: dict[str, object],
    ) -> list[tuple[str, str]]:
        cargo_value = reporting_context.get("total_cargo_weight")
        cargo_text = str(cargo_value) if cargo_value not in (None, "") else "Manual completion required"
        return [
            ("Vessel code", self._string_value(vessel_particulars.get("vesselCode"), default="Not available in workspace")),
            ("Vessel name", self._string_value(vessel_particulars.get("vesselName"), default="Not available in workspace")),
            ("IMO number", self._string_value(vessel_particulars.get("imoNumber"), default="Not available in workspace")),
            ("Flag", self._string_value(vessel_particulars.get("flags"), default="Not available in workspace")),
            (
                "Classification society",
                self._string_value(vessel_particulars.get("ClassificationSociety"), default="Not available in workspace"),
            ),
            ("Gross tonnage", self._string_value(vessel_particulars.get("grt"), default="Not available in workspace")),
            ("Net tonnage", self._string_value(vessel_particulars.get("nrt"), default="Not available in workspace")),
            ("Deadweight", self._string_value(vessel_particulars.get("deadweight"), default="Not available in workspace")),
            ("Cargo quantity", cargo_text),
            ("Crew complement", "Manual completion required"),
            ("Ship owner", self._string_value(vessel_particulars.get("ShipOwner"), default="Not available in workspace")),
            (
                "Ship management",
                self._string_value(vessel_particulars.get("ShipManagement"), default="Not available in workspace"),
            ),
        ]

    def _build_appendix3_rows(self, incident: Incident) -> list[tuple[str, str]]:
        fact_rows = list(incident.facts.all().order_by("sequence_index", "id"))
        cause_rows = list(incident.cause_tags.all().order_by("id"))
        recommendation_rows = list(incident.recommendations.filter(is_deleted=False).order_by("id"))

        sequence_summary = " | ".join(row.fact_text.strip() for row in fact_rows[:3] if (row.fact_text or "").strip())
        if not sequence_summary:
            sequence_summary = incident.narrative or "Narrative not recorded."

        contributing_factors = ", ".join(
            f"{row.causal_layer.title()} {row.mscat_subcode_id}" for row in cause_rows[:6]
        ) or "No cause-tree rows recorded."

        recommendation_summary = "; ".join(
            (row.title or "").strip() for row in recommendation_rows[:4] if (row.title or "").strip()
        ) or "No recommendation titles recorded."

        return [
            ("Sequence of events", sequence_summary),
            ("Hazard / casualty narrative", incident.narrative or "Narrative not recorded."),
            ("Contributing factors", contributing_factors),
            ("Corrective action posture", recommendation_summary),
            ("Cause-tree depth", str(len(cause_rows))),
        ]

    def _build_appendix4_rows(
        self,
        incident: Incident,
        *,
        reporting_context: dict[str, object],
    ) -> list[tuple[str, str]]:
        latitude = reporting_context.get("latitude")
        longitude = reporting_context.get("longitude")
        return [
            (
                "Daily Report source",
                self._string_value(reporting_context.get("source_reference"), default="No Daily Report match"),
            ),
            ("Matched report date", self._string_value(reporting_context.get("report_date"), default="Not available")),
            ("Latitude", self._string_value(latitude, default=self._string_value(incident.latitude, default="Not available"))),
            (
                "Longitude",
                self._string_value(longitude, default=self._string_value(incident.longitude, default="Not available")),
            ),
            ("Voyage number", self._string_value(reporting_context.get("voyage_no"), default="Not available")),
            ("Voyage condition", self._string_value(reporting_context.get("voy_condition"), default="Not available")),
            ("Weather remarks", self._string_value(reporting_context.get("weather_remarks"), default="Not available")),
            ("Wind force", self._string_value(reporting_context.get("wind_force"), default="Not available")),
            ("Sea state", self._string_value(reporting_context.get("sea_state"), default="Not available")),
            ("Current strength", self._string_value(reporting_context.get("current_strength"), default="Not available")),
        ]

    def _build_appendix5_rows(
        self,
        incident: Incident,
        *,
        vessel_particulars: dict[str, object],
        reporting_context: dict[str, object],
    ) -> list[tuple[str, str, str]]:
        incident_type_name = self._lookup_master_value(
            table_name="master_safety_incident_type",
            key_column="legacy_int_id",
            value_column="type_name",
            key_value=incident.incident_type_id,
        )
        loss_type_name = self._lookup_master_value(
            table_name="master_loss_types",
            key_column="loss_type_id",
            value_column="loss_type_name",
            key_value=incident.loss_type_primary_id,
        )
        rows = [
            ("Field 01 - IMO classifier", incident.imo_classifier or "Not assigned", "vims_safety_incident.imo_classifier"),
            (
                "Field 02 - Incident type",
                incident_type_name or self._string_value(incident.incident_type_id, default="Not assigned"),
                "master_safety_incident_type",
            ),
            (
                "Field 03 - Primary loss type",
                loss_type_name or self._string_value(incident.loss_type_primary_id, default="Not assigned"),
                "master_loss_types",
            ),
            ("Field 04 - Risk band", incident.risk_band or "Unassigned", "vims_safety_incident.risk_band"),
            (
                "Field 05 - Investigation depth",
                incident.investigation_depth or "Not assigned",
                "vims_safety_incident.investigation_depth",
            ),
            ("Field 06 - Position source", incident.position_source or "Not assigned", "vims_safety_incident.position_source"),
            (
                "Field 07 - Awaiting Daily Report match",
                "Yes" if incident.awaiting_daily_report_match else "No",
                "vims_safety_incident.awaiting_daily_report_match",
            ),
            (
                "Field 08 - First-hour checklist",
                "Complete" if incident.first_hour_checklist_done else "Pending",
                "vims_safety_incident.first_hour_checklist_done",
            ),
            (
                "Field 09 - Marine documents checklist",
                "Complete" if incident.marine_docs_checklist_done else "Pending",
                "vims_safety_incident.marine_docs_checklist_done",
            ),
            (
                "Field 10 - Chain of custody status",
                "Complete" if incident.chain_of_custody_ok else "Pending",
                "vims_safety_incident.chain_of_custody_ok",
            ),
            (
                "Field 11 - Cargo evidence applicable",
                "Yes" if incident.cargo_evidence_applicable else "No",
                "vims_safety_incident.cargo_evidence_applicable",
            ),
            (
                "Field 12 - Health / fatigue applicable",
                "Yes" if incident.health_fatigue_applicable else "No",
                "vims_safety_incident.health_fatigue_applicable",
            ),
            (
                "Field 13 - Causal layering complete",
                "Yes" if incident.causal_layering_complete else "No",
                "vims_safety_incident.causal_layering_complete",
            ),
            (
                "Field 14 - ALARP attested",
                "Yes" if incident.alarp_attested else "No",
                "vims_safety_incident.alarp_attested",
            ),
            (
                "Field 15 - Bias guard attestations",
                incident.bias_guard_attestations or "Not recorded",
                "vims_safety_incident.bias_guard_attestations",
            ),
            (
                "Field 16 - Reporter rank",
                self._string_value(incident.reporter_rank, default="Not recorded"),
                "vims_safety_incident.reporter_rank",
            ),
            (
                "Field 17 - Reporter department",
                self._string_value(incident.reporter_department, default="Not recorded"),
                "vims_safety_incident.reporter_department",
            ),
            (
                "Field 18 - DPA notified",
                self._string_value(self._serialize_datetime(incident.dpa_notified_at), default="Not recorded"),
                "vims_safety_incident.dpa_notified_at",
            ),
            (
                "Field 19 - FM notified",
                self._string_value(self._serialize_datetime(incident.fm_notified_at), default="Not recorded"),
                "vims_safety_incident.fm_notified_at",
            ),
            (
                "Field 20 - Office notified",
                self._string_value(self._serialize_datetime(incident.office_notified_at), default="Not recorded"),
                "vims_safety_incident.office_notified_at",
            ),
            (
                "Field 21 - Vessel flag",
                self._string_value(vessel_particulars.get("flags"), default="Not available in workspace"),
                "VesselData.flags",
            ),
            (
                "Field 22 - Vessel class",
                self._string_value(vessel_particulars.get("ClassificationSociety"), default="Not available in workspace"),
                "VesselData.ClassificationSociety",
            ),
            (
                "Field 23 - Vessel gross tonnage",
                self._string_value(vessel_particulars.get("grt"), default="Not available in workspace"),
                "VesselData.grt",
            ),
            (
                "Field 24 - Vessel deadweight",
                self._string_value(vessel_particulars.get("deadweight"), default="Not available in workspace"),
                "VesselData.deadweight",
            ),
            (
                "Field 25 - Cargo quantity",
                self._string_value(reporting_context.get("total_cargo_weight"), default="Not available"),
                f"{reporting_context.get('source_table') or 'Daily Report'}.TotalCargoWeight",
            ),
            (
                "Field 26 - Voyage condition",
                self._string_value(reporting_context.get("voy_condition"), default="Not available"),
                f"{reporting_context.get('source_table') or 'Daily Report'}.VoyCondition",
            ),
            (
                "Field 27 - Weather remarks",
                self._string_value(reporting_context.get("weather_remarks"), default="Not available"),
                f"{reporting_context.get('source_table') or 'Daily Report'}.WeatherRemarks",
            ),
            (
                "Field 28 - Wind force",
                self._string_value(reporting_context.get("wind_force"), default="Not available"),
                f"{reporting_context.get('source_table') or 'Daily Report'}.WindForce",
            ),
            (
                "Field 29 - Sea state",
                self._string_value(reporting_context.get("sea_state"), default="Not available"),
                f"{reporting_context.get('source_table') or 'Daily Report'}.SeaState",
            ),
            (
                "Field 30 - Current strength",
                self._string_value(reporting_context.get("current_strength"), default="Not available"),
                f"{reporting_context.get('source_table') or 'Daily Report'}.CurrentStrength",
            ),
        ]
        return rows

    def _load_vessel_particulars(self, incident: Incident) -> dict[str, object]:
        connection = connections[self.model_class.objects.db]
        if "VesselData" not in set(connection.introspection.table_names()):
            return {}

        vessel_identifier = str(incident.vessel_id)
        if connection.vendor == "microsoft":
            query = """
                SELECT TOP 1
                    CAST(id AS VARCHAR(64)) AS vessel_pk,
                    vesselCode,
                    vesselName,
                    imoNumber,
                    flags,
                    ClassificationSociety,
                    grt,
                    nrt,
                    deadweight,
                    LastPortofcall,
                    ShipOwner,
                    ShipManagement
                FROM dbo.VesselData
                WHERE (CAST(id AS VARCHAR(64)) = %s OR vesselCode = %s)
                  AND ISNULL(is_deleted, 0) = 0
                ORDER BY CASE WHEN CAST(id AS VARCHAR(64)) = %s THEN 0 ELSE 1 END
            """
            rows = self._run_query(query, (vessel_identifier, vessel_identifier, vessel_identifier))
        else:
            query = """
                SELECT
                    CAST(id AS TEXT) AS vessel_pk,
                    vesselCode,
                    vesselName,
                    imoNumber,
                    flags,
                    ClassificationSociety,
                    grt,
                    nrt,
                    deadweight,
                    LastPortofcall,
                    ShipOwner,
                    ShipManagement
                FROM VesselData
                WHERE (CAST(id AS TEXT) = %s OR vesselCode = %s)
                LIMIT 1
            """
            rows = self._run_query(query, (vessel_identifier, vessel_identifier))
        return rows[0] if rows else {}

    def _load_reporting_context(
        self,
        incident: Incident,
        *,
        vessel_particulars: dict[str, object],
    ) -> dict[str, object]:
        vessel_lookup = str(vessel_particulars.get("vesselCode") or incident.vessel_id or "")
        fetch_result = self.position_fetcher.fetch_position(vessel_id=vessel_lookup, timestamp=incident.occurred_at)
        context = {
            "latitude": fetch_result.get("latitude") or self._decimal_or_none(incident.latitude),
            "longitude": fetch_result.get("longitude") or self._decimal_or_none(incident.longitude),
            "position_source": fetch_result.get("position_source") or incident.position_source,
            "position_daily_report_id": fetch_result.get("position_daily_report_id") or incident.position_daily_report_id,
            "report_date": fetch_result.get("report_date"),
            "source_reference": fetch_result.get("source_reference"),
            "source_table": fetch_result.get("source_table"),
        }
        if not fetch_result.get("matched"):
            return context

        source_table = str(fetch_result.get("source_table") or "")
        source_reference = str(fetch_result.get("source_reference") or "")
        try:
            source_row = self._load_reporting_source_row(source_table, source_reference)
        except Exception:
            source_row = {}
        source_row.update(context)
        return source_row

    def _load_reporting_source_row(self, source_table: str, source_reference: str) -> dict[str, object]:
        column_map = self._report_column_map.get(source_table)
        if column_map is None:
            return {}

        connection = connections[self.model_class.objects.db]
        if source_table not in set(connection.introspection.table_names()):
            return {}

        identifier = source_reference.partition(":")[2]
        if not identifier:
            return {}

        lat_deg, lat_min, lat_hemi = column_map["lat_columns"]
        lon_deg, lon_min, lon_hemi = column_map["lon_columns"]
        id_column = "auto_id" if identifier.isdigit() else "id"
        table_name = f"dbo.{source_table}" if connection.vendor == "microsoft" else source_table
        top_clause = "TOP 1" if connection.vendor == "microsoft" else ""
        limit_clause = "" if connection.vendor == "microsoft" else " LIMIT 1"

        query = f"""
            SELECT {top_clause}
                ReportDate AS report_date,
                VoyageNo AS voyage_no,
                VoyCondition AS voy_condition,
                WeatherRemarks AS weather_remarks,
                WindForce AS wind_force,
                SeaState AS sea_state,
                CurrentStrength AS current_strength,
                TotalCargoWeight AS total_cargo_weight,
                {lat_deg} AS lat_deg,
                {lat_min} AS lat_min,
                {lat_hemi} AS lat_hemi,
                {lon_deg} AS lon_deg,
                {lon_min} AS lon_min,
                {lon_hemi} AS lon_hemi
            FROM {table_name}
            WHERE {id_column} = %s{limit_clause}
        """
        rows = self._run_query(query, (identifier,))
        if not rows:
            return {}

        row = rows[0]
        latitude = self.position_fetcher._to_signed_decimal(row.get("lat_deg"), row.get("lat_min"), row.get("lat_hemi"))
        longitude = self.position_fetcher._to_signed_decimal(row.get("lon_deg"), row.get("lon_min"), row.get("lon_hemi"))
        row["latitude"] = latitude
        row["longitude"] = longitude
        return row

    def _lookup_master_value(
        self,
        *,
        table_name: str,
        key_column: str,
        value_column: str,
        key_value,
    ) -> str | None:
        if key_value in (None, ""):
            return None

        connection = connections[self.model_class.objects.db]
        if table_name not in set(connection.introspection.table_names()):
            return None

        qualified_name = f"dbo.{table_name}" if connection.vendor == "microsoft" else table_name
        top_clause = "TOP 1" if connection.vendor == "microsoft" else ""
        limit_clause = "" if connection.vendor == "microsoft" else " LIMIT 1"
        query = f"SELECT {top_clause} {value_column} AS resolved_value FROM {qualified_name} WHERE {key_column} = %s{limit_clause}"
        rows = self._run_query(query, (key_value,))
        if not rows:
            return None
        return self._string_value(rows[0].get("resolved_value"), default=None)

    def _persist_content(self, incident: Incident, content: bytes) -> str:
        export_dir = self.export_root / str(incident.vessel_id) / "exports"
        export_dir.mkdir(parents=True, exist_ok=True)
        output_path = export_dir / self._build_file_name(incident)
        output_path.write_bytes(content)
        return str(output_path.resolve())

    def _record_export_history(self, incident: Incident, *, export_path: str, user) -> None:
        SafetyFieldHistory.objects.create(
            parent_table=incident._meta.db_table,
            parent_id=incident.pk,
            field_name="incident_msc_mepc3_export",
            old_value=None,
            new_value={
                "content_type": self.content_type,
                "download_path": f"/api/safety/export/msc-mepc-3/{incident.public_id}/",
                "export_path": export_path,
                "file_name": self._build_file_name(incident),
            },
            change_reason="MSC-MEPC.3/Circ.4 PDF generated.",
            actor_user_id=resolve_actor_id(user),
            actor_role_code=resolve_actor_role(user),
            schema_version=incident.schema_version or 1,
        )

    @staticmethod
    def _build_file_name(incident: Incident) -> str:
        safe_number = "".join(char if char.isalnum() or char in {"-", "_"} else "-" for char in incident.incident_number)
        while "--" in safe_number:
            safe_number = safe_number.replace("--", "-")
        return f"{safe_number.strip('-')}-msc-mepc3-circ4.pdf"

    def _run_query(self, query: str, params: tuple[object, ...]) -> list[dict[str, object]]:
        connection = connections[self.model_class.objects.db]
        with connection.cursor() as cursor:
            cursor.execute(query, params)
            if not cursor.description:
                return []
            columns = [column[0] for column in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

    @staticmethod
    def _decimal_or_none(value) -> float | None:
        if value in (None, ""):
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _string_value(value, *, default: str | None) -> str | None:
        if value in (None, ""):
            return default
        return str(value).strip()
