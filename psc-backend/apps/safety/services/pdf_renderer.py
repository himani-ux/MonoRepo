from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from collections import defaultdict
import json
import os
from pathlib import Path
from typing import Iterable
from urllib.parse import quote

from django.db import DatabaseError, connections
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from apps.safety.models import (
    CorrectiveAction,
    IncidentCauseTag,
    ExternalPartyInjury,
    Incident,
    IncidentLossEvaluation,
    IncidentWeatherOption,
    IncidentPhaseLog,
    MasterLossType,
    MasterMscatTaxonomy,
    MasterSafetyIncidentType,
    Recommendation,
    SafetyFieldHistory,
    SCMMeeting,
    SOIFinding,
    SOIInspection,
    WitnessInterview,
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
from apps.safety.services.incident_weather_schema_guard import WEATHER_OPTION_SEEDS
from apps.safety.services.pdf_post_process import PdfPostProcessor
from apps.safety.services.pdf_templates.incident_10_section import (
    IncidentPdfContext,
    IncidentPdfDetailBlock,
    IncidentPdfSignatureRow,
    IncidentTenSectionTemplate,
)
from apps.safety.services.pdf_templates.msc_mepc3_circ4 import MscMepc3Circ4PdfContext, MscMepc3Circ4Template
from apps.safety.services.pdf_templates.near_miss_lightweight import (
    NearMissCauseFactorPdfRow,
    NearMissLightweightPdfContext,
    NearMissLightweightTemplate,
    NearMissPdfSignatureRow,
)
from apps.safety.services.pdf_templates.scm_10_section_legacy import (
    SCMLegacyAttendanceRow,
    SCMLegacyClosedItem,
    SCMLegacyPdfContext,
    SCMLegacySectionRow,
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


INCIDENT_PDF_SECTION_LABELS = {
    "summary": "Summary",
    "reporter_details": "Reporter Details",
    "injury_details": "Injury Details",
    "root_cause": "Root Cause Analysis",
    "corrective_preventive_actions": "Corrective and Preventive Actions",
    "evidence_documents": "Evidence (Documents)",
    "lessons_learned": "Lessons Learned",
    "signature": "Signature",
    "estimated_cost": "Estimated Cost",
}
DEFAULT_INCIDENT_PDF_SECTION_KEYS = tuple(INCIDENT_PDF_SECTION_LABELS)
ATTACHMENT_FILE_SUFFIXES = {".csv", ".doc", ".docx", ".gif", ".jpeg", ".jpg", ".pdf", ".png", ".txt", ".xls", ".xlsx"}


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
        incident_id,
        viewer_user,
        persist: bool = True,
        included_sections: Iterable[str] | None = None,
    ) -> IncidentPdfRenderResult:
        incident = self._get_incident(incident_id)
        self._validate_exportable(incident)
        section_keys = self.normalize_section_keys(included_sections)

        context = self._build_context(incident, viewer_user=viewer_user, included_sections=section_keys)
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
            download_path=f"/api/safety/incidents/{incident.id}/pdf/",
            export_path=export_path,
            file_name=self._build_file_name(incident),
            incident_id=incident.pk,
            section_titles=[INCIDENT_PDF_SECTION_LABELS[key] for key in section_keys],
        )

    @staticmethod
    def normalize_section_keys(section_keys: Iterable[str] | None) -> tuple[str, ...]:
        if section_keys is None:
            return DEFAULT_INCIDENT_PDF_SECTION_KEYS
        normalized = tuple(dict.fromkeys(str(key).strip() for key in section_keys if str(key).strip()))
        if not normalized:
            return DEFAULT_INCIDENT_PDF_SECTION_KEYS
        invalid = [key for key in normalized if key not in INCIDENT_PDF_SECTION_LABELS]
        if invalid:
            raise ValidationError(f"Unknown incident PDF section(s): {', '.join(invalid)}.")
        return normalized

    def _get_incident(self, incident_id: int) -> Incident:
        return (
            self.model_class.objects.select_related(
                "phase5_assessment",
                "blame_override",
                "external_party_injury",
                "loss_evaluation",
            )
            .prefetch_related(
                "bias_guard_responses",
                "chain_of_custody_rows",
                "cause_tags__source_fact",
                "evidence_deadline_tasks",
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

    def _build_context(self, incident: Incident, *, viewer_user=None, included_sections: Iterable[str] | None = None) -> IncidentPdfContext:
        assessment = getattr(incident, "phase5_assessment", None)
        recommendations = list(incident.recommendations.filter(is_deleted=False).order_by("id"))
        vessel_display = resolve_vessel_display(incident.vessel_id, user=viewer_user)
        vessel_name = vessel_display["vessel_display_name"] or str(incident.vessel_id)
        return IncidentPdfContext(
            incident_id=incident.pk,
            incident_number=incident.incident_number,
            vessel_id=vessel_name,
            current_phase=incident.current_phase,
            risk_band=incident.risk_band,
            imo_classifier=incident.imo_classifier,
            occurred_at=self._format_pdf_datetime(incident.occurred_at),
            reported_at=self._format_pdf_datetime(incident.reported_at),
            narrative=incident.narrative or "Narrative not recorded.",
            generated_at=self._format_pdf_datetime(timezone.now()) or "",
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
            report_title=self._build_report_title(incident),
            section_titles=list(self.template.SECTION_TITLES),
            classification_rows=self._build_classification_rows(incident, vessel_name=vessel_name),
            summary_blocks=self._build_summary_blocks(incident),
            investigator_blocks=self._build_investigator_blocks(incident),
            reporter_blocks=self._build_reporter_blocks(incident),
            injury_detail_blocks=self._build_injury_detail_blocks(incident),
            estimated_cost_blocks=self._build_estimated_cost_blocks(incident),
            evidence_blocks=self._build_evidence_blocks(incident),
            cause_blocks=self._build_cause_blocks(incident, assessment=assessment),
            factor_blocks=self._build_factor_blocks(incident, assessment=assessment),
            action_blocks=self._build_action_blocks_detail(recommendations),
            lesson_blocks=self._build_lesson_blocks(recommendations),
            closure_blocks=self._build_closure_blocks(incident),
            notification_blocks=[],
            appendix_blocks=[],
            included_section_keys=list(self.normalize_section_keys(included_sections)),
        )

    def _build_summary_blocks(self, incident: Incident) -> list[IncidentPdfDetailBlock]:
        weather_block = self._build_weather_condition_block(incident)
        return [weather_block] if weather_block.rows else []

    @staticmethod
    def _external_party_injury_record(incident: Incident) -> ExternalPartyInjury | None:
        try:
            return incident.external_party_injury
        except ExternalPartyInjury.DoesNotExist:
            return None
        except AttributeError:
            return None

    @staticmethod
    def _loss_evaluation_record(incident: Incident) -> IncidentLossEvaluation | None:
        try:
            return incident.loss_evaluation
        except IncidentLossEvaluation.DoesNotExist:
            return None
        except AttributeError:
            return None

    @classmethod
    def _build_report_title(cls, incident: Incident) -> str:
        return "Injury Report" if cls._external_party_injury_record(incident) else "Incident Report"

    def _build_classification_rows(self, incident: Incident, *, vessel_name: str) -> list[tuple[str, str]]:
        loss_values = [
            self._loss_type_name(incident.loss_type_primary_id),
            self._loss_type_name(incident.loss_type_secondary_id),
            self._loss_type_name(incident.loss_type_tertiary_id),
        ]
        selected_loss_values = [value for value in loss_values if value != "Not recorded"]
        if incident.loss_type_other:
            selected_loss_values.append(f"Other - {incident.loss_type_other}")
        incident_type_name = self._incident_type_name(incident.incident_type_id)
        if incident.incident_type_other:
            incident_type_name = f"{incident_type_name} - {incident.incident_type_other}"
        return [
            ("Incident number", self._display(incident.incident_number)),
            ("Vessel", self._display(vessel_name)),
            ("Status", self._display(incident.state)),
            ("Risk band", self._display(incident.risk_band)),
            ("Incident type", incident_type_name),
            ("Type of loss", ", ".join(selected_loss_values) if selected_loss_values else "Not recorded"),
            ("Was a Risk Assessment carried out?", self._choice_label(incident.risk_assessment_carried_out)),
            ("Was Toolbox Meeting carried out?", self._choice_label(incident.toolbox_meeting_carried_out)),
            ("Was a Permit Issue?", self._choice_label(incident.permit_issued)),
            ("Type of Activity", self._display(incident.activity_type)),
            ("Occurred at", self._format_pdf_datetime(incident.occurred_at) or "Not recorded"),
            ("Reported at", self._format_pdf_datetime(incident.reported_at) or "Not recorded"),
            ("Latitude", self._display(incident.latitude)),
            ("Longitude", self._display(incident.longitude)),
            ("Shore assistance required", self._yes_no(incident.shore_assistance_required)),
            ("Vessel location", self._display(self._vessel_location_text(incident))),
            ("Location on Board", self._display(incident.onboard_location)),
            ("Departure date", self._display(incident.departure_date)),
            ("Vessel condition", self._choice_label(incident.vessel_condition)),
            ("Office informed?", self._yes_no(incident.office_notified)),
            ("Communication mode", self._choice_label(incident.office_notification_mode)),
            ("Generated at", self._format_pdf_datetime(timezone.now()) or ""),
        ]

    def _build_closure_blocks(self, incident: Incident) -> list[IncidentPdfDetailBlock]:
        blocks = []
        office_block = self._detail_block(
            "Office comments/ lesson learnt",
            [
                ("", self._display(incident.office_comment)),
            ],
        )
        if office_block.rows:
            blocks.append(office_block)
        return blocks

    def _build_investigator_blocks(self, incident: Incident) -> list[IncidentPdfDetailBlock]:
        blocks: list[IncidentPdfDetailBlock] = []
        blocks.extend(self._build_reporter_blocks(incident))
        blocks.extend(self._build_injury_detail_blocks(incident))
        blocks.extend(self._build_estimated_cost_blocks(incident))

        office_block = self._detail_block(
                "Office acceptance and closure",
                [
                    ("PIC / DPA accepted by", self._display(incident.dpa_accepted_by)),
                    ("PIC / DPA accepted at", self._format_pdf_datetime(incident.dpa_accepted_at) or "Not recorded"),
                ],
            )
        if office_block.rows:
            blocks.append(office_block)

        weather_block = self._build_weather_condition_block(incident)
        if weather_block.rows:
            blocks.append(weather_block)
        return blocks

    def _build_reporter_blocks(self, incident: Incident) -> list[IncidentPdfDetailBlock]:
        block = self._detail_block(
            "Reporter details",
            [
                ("Reporter name", self._display(incident.reporter_name)),
                ("Reporter rank", self._display(incident.reporter_rank)),
                ("Reporter department", self._display(incident.reporter_department)),
                ("Reporter email", self._display(incident.reporter_email)),
            ],
        )
        return [block] if block.rows else []

    def _build_injury_detail_blocks(self, incident: Incident) -> list[IncidentPdfDetailBlock]:
        return [
            block
            for block in self._build_injury_blocks(incident)
            if block.heading != "Estimated injury costs"
        ]

    def _build_estimated_cost_blocks(self, incident: Incident) -> list[IncidentPdfDetailBlock]:
        loss_evaluation_blocks = self._build_loss_evaluation_blocks(incident)
        if loss_evaluation_blocks:
            return loss_evaluation_blocks
        return [
            block
            for block in self._build_injury_blocks(incident)
            if block.heading == "Estimated injury costs"
        ]

    def _build_injury_blocks(self, incident: Incident) -> list[IncidentPdfDetailBlock]:
        injury = self._external_party_injury_record(incident)
        if injury is None:
            return []

        blocks: list[IncidentPdfDetailBlock] = []
        for block in [
            self._detail_block(
                "Injury details",
                [
                    ("Injured person type", self._choice_label(injury.injured_person_type)),
                    ("Party name", self._display(injury.party_name)),
                    ("Party type", self._choice_label(injury.party_type)),
                    ("Company name", self._display(injury.company_name)),
                    ("Severity", self._display(injury.severity)),
                    ("Crew rank", self._display(injury.crew_rank)),
                    ("Crew age", self._display(injury.crew_age)),
                    ("Type of activity", self._display(injury.crew_activity_type)),
                    (
                        "Shore assistance required",
                        self._yes_no(
                            incident.shore_assistance_required
                            if incident.shore_assistance_required is not None
                            else injury.shore_assistance_required
                        ),
                    ),
                    ("Vessel location", self._display(self._vessel_location_text(incident) or injury.vessel_location)),
                    ("Location on Board", self._display(incident.onboard_location or injury.onboard_location)),
                    ("Departure date", self._display(incident.departure_date or injury.departure_date)),
                    ("Vessel condition", self._choice_label(incident.vessel_condition or injury.vessel_condition)),
                    ("Nature of injury", self._display(injury.nature_of_injury)),
                    ("Source of injury", self._display(injury.source_of_injury)),
                    ("Affected body areas", self._display(injury.affected_body_areas)),
                    ("First aid details", self._display(injury.first_aid_details)),
                    ("Notes", self._display(injury.notes)),
                ],
            ),
            self._detail_block(
                "Injury investigation",
                [
                    ("Why it happened", self._display(injury.why_it_happened_analysis)),
                    ("Regulation or procedure breach", self._display(injury.regulation_or_procedure_breach)),
                    ("Risk assessment carried out", self._choice_label(injury.risk_assessment_carried_out)),
                    ("Toolbox meeting carried out", self._choice_label(injury.toolbox_meeting_carried_out)),
                    ("Prevention action taken / required", self._display(injury.prevention_action_taken_required)),
                ],
            ),
            self._detail_block(
                "OCIMF injury reporting",
                [
                    ("Fatality", self._yes_no(injury.ocimf_fatality)),
                    ("Permanent total disability", self._yes_no(injury.ocimf_permanent_total_disability)),
                    ("Permanent partial disability", self._yes_no(injury.ocimf_permanent_partial_disability)),
                    ("Lost workday case", self._yes_no(injury.ocimf_lost_workday_case)),
                    ("Restricted workday case", self._yes_no(injury.ocimf_restricted_workday_case)),
                    ("Medical treatment case", self._yes_no(injury.ocimf_medical_treatment_case)),
                    ("First aid case", self._yes_no(injury.ocimf_first_aid_case)),
                ],
            ),
            self._detail_block(
                "Estimated injury costs",
                [
                    ("Medicines onboard", self._display(injury.cost_medicines_onboard)),
                    ("Doctor visits", self._display(injury.cost_doctor_visits)),
                    ("Repatriation", self._display(injury.cost_repatriation)),
                    ("Evacuation", self._display(injury.cost_evacuation)),
                    ("Off hire", self._display(injury.cost_off_hire)),
                    ("Vessel delays", self._display(injury.cost_vessel_delays)),
                    ("Man hours lost", self._display(injury.cost_man_hours_lost)),
                    ("Deviation", self._display(injury.cost_deviation)),
                    ("Miscellaneous", self._display(injury.cost_miscellaneous)),
                    ("Miscellaneous reason", self._display(injury.miscellaneous_expenses_reason)),
                    ("Total estimated cost", self._display(injury.total_estimated_cost)),
                ],
            ),
        ]:
            if block.rows:
                blocks.append(block)
        return blocks

    def _build_loss_evaluation_blocks(self, incident: Incident) -> list[IncidentPdfDetailBlock]:
        loss = self._loss_evaluation_record(incident)
        if loss is None:
            return []

        saved_report_type = getattr(loss, "report_type", None)
        is_injury_report = (
            saved_report_type == IncidentLossEvaluation.ReportType.INJURY
            if saved_report_type
            else self._external_party_injury_record(incident) is not None
        )
        blocks = [
            self._detail_block(
                "Risk Assessment",
                [
                    ("Consequence", self._choice_label(loss.consequence)),
                    ("Likelihood", self._choice_label(loss.likelihood)),
                    ("Risk level", self._choice_label(loss.risk_level)),
                ],
            ),
            self._detail_block(
                "Details",
                [
                    ("Name of master", self._display(loss.name_of_master)),
                    ("Name of Chief Engineer", self._display(loss.name_of_chief_engineer)),
                    *(
                        [
                            (
                                "Code of Safe Working Practices",
                                self._display(loss.safe_working_practice),
                            ),
                            ("Man hours worked", self._display(loss.man_hours_worked)),
                            ("Hours worked on the previous day", self._display(loss.hours_worked_previous_day)),
                            ("Hours of rest in the last 96 hours", self._display(loss.hours_rest_last_96_hours)),
                        ]
                        if is_injury_report
                        else [
                            ("Type of Repairs", self._choice_label(loss.repair_type)),
                            (
                                "Details of temporary / permanent repairs done / required",
                                self._display(loss.repair_details),
                            ),
                            (
                                "Details of last overhaul / maintenance / survey of equipment",
                                self._display(loss.last_overhaul_maintenance_survey_details),
                            ),
                        ]
                    ),
                ],
            ),
            self._detail_block(
                "Cost Evaluation",
                [
                    ("Delays to Vessel (if any)", self._display(loss.delay_to_vessel)),
                    *(
                        [
                            ("Man hours lost", self._display(loss.injury_man_hours_lost)),
                            ("Reasons", self._display(loss.injury_reasons)),
                            ("Off Hire", self._yes_no(loss.off_hire)),
                            ("Repatriation", self._yes_no(loss.repatriation)),
                            ("Hospitalization", self._yes_no(loss.hospitalization)),
                            ("Deviation", self._yes_no(loss.deviation)),
                            ("Evacuation", self._yes_no(loss.evacuation)),
                        ]
                        if is_injury_report
                        else [
                            ("Reasons for delay", self._display(loss.delay_reason)),
                            ("Man hours lost in repairs", self._display(loss.repair_man_hours_lost)),
                            ("Materials used for repairs onboard", self._display(loss.materials_used_repairs_onboard)),
                            ("Specify Details", self._display(loss.materials_specify_details)),
                            ("Reasons", self._display(loss.materials_reason)),
                            ("Deviation", self._yes_no(loss.deviation)),
                            ("Off Hire", self._yes_no(loss.off_hire)),
                        ]
                    ),
                ],
            ),
            self._detail_block(
                "Estimated Costs",
                (
                    [
                        ("Cost for Medicines Given Onboard", self._display(loss.cost_medicines_onboard)),
                        ("Cost for Visits to Doctors", self._display(loss.cost_doctor_visits)),
                        ("Cost for Repatriation", self._display(loss.cost_repatriation)),
                        ("Cost for Evacuation", self._display(loss.cost_evacuation)),
                        ("Cost for Delays to Vessel if any", self._display(loss.cost_injury_delay)),
                        ("Cost for Man Hours Lost", self._display(loss.cost_injury_man_hours)),
                        ("Cost for Deviation", self._display(loss.cost_injury_deviation)),
                        ("Cost for Miscellaneous Expenses", self._display(loss.cost_injury_miscellaneous)),
                        ("Total Estimated cost", self._display(loss.injury_total_estimated_cost)),
                        (
                            "Reasons for Miscellaneous Expenses",
                            self._display(loss.injury_miscellaneous_expenses_reason),
                        ),
                    ]
                    if is_injury_report
                    else [
                        ("Estimated Cost for Off Hire", self._display(loss.estimated_cost_off_hire)),
                        ("Estimated Cost for Delays to Vessel if any", self._display(loss.estimated_cost_delay)),
                        ("Estimated Cost for Man Hour Lost", self._display(loss.estimated_cost_man_hours)),
                        ("Estimated Cost for Deviation", self._display(loss.estimated_cost_deviation)),
                        ("Estimated Cost for Materials used in Repairs", self._display(loss.estimated_cost_materials)),
                        ("Estimated Cost for Miscellaneous Expenses", self._display(loss.estimated_cost_miscellaneous)),
                        ("Total Estimated cost", self._display(loss.total_estimated_cost)),
                        ("Reasons for Miscellaneous Expenses", self._display(loss.miscellaneous_expenses_reason)),
                    ]
                ),
            ),
        ]
        return [block for block in blocks if block.rows]

    def _build_weather_condition_block(self, incident: Incident) -> IncidentPdfDetailBlock:
        return self._detail_block(
            "Weather Condition",
            [
                ("Visibility", self._weather_option_label(incident.weather_visibility_id)),
                ("Precipitation", self._weather_option_label(incident.weather_precipitation_id)),
                ("Sea State", self._weather_option_label(incident.weather_sea_state_id)),
                ("Wind Scale", self._weather_option_label(incident.weather_wind_scale_id)),
                ("Wind Direction", self._weather_option_label(incident.weather_wind_direction_id)),
                ("Source of Lighting", self._weather_option_label(incident.weather_lighting_source_id)),
                ("Current Direction", self._weather_option_label(incident.weather_current_direction_id)),
                ("Current Strength (knots)", self._display(incident.weather_current_strength_knots)),
                ("Ambient Temperature (Deg C)", self._display(incident.weather_ambient_temperature_c)),
                ("Ice condition on-board", self._weather_option_label(incident.weather_ice_condition_onboard_id)),
                ("Ice condition at sea", self._weather_option_label(incident.weather_ice_condition_at_sea_id)),
                ("Light condition", self._weather_option_label(incident.weather_light_condition_id)),
            ],
        )

    def _build_evidence_blocks(self, incident: Incident) -> list[IncidentPdfDetailBlock]:
        blocks = self._build_evidence_document_blocks(incident)
        blocks.extend(self._build_witness_note_blocks(incident))
        return blocks

    def _build_witness_note_blocks(self, incident: Incident) -> list[IncidentPdfDetailBlock]:
        blocks: list[IncidentPdfDetailBlock] = []
        interviews = list(incident.witness_interviews.all().order_by("created_date", "id"))
        for interview in interviews:
            heading = "Witness Statement"
            witness_name = self._clean_text(interview.witness_name)
            if witness_name:
                heading = f"Witness Statement - {witness_name}"
            block = self._detail_block(
                heading,
                [
                    (
                        "Witness statement attachment",
                        self._witness_statement_attachment_link(incident, interview),
                    ),
                    ("Remark", self._display(interview.conclusion_notes)),
                ],
            )
            if block.rows:
                blocks.append(block)
        return blocks

    def _build_evidence_document_blocks(self, incident: Incident) -> list[IncidentPdfDetailBlock]:
        blocks: list[IncidentPdfDetailBlock] = []
        for item in incident.evidence_items.all().order_by("created_date", "id"):
            attachment_links = self._attachment_links_for_item(incident, item)
            title = self._clean_text(item.title)
            description = self._clean_text(item.description)
            if attachment_links:
                meaningful_title = self._meaningful_evidence_title(title, attachment_links)
                rows: list[tuple[str, str]] = []
                if description:
                    rows.append(("Description", description))
                rows.append(("File", attachment_links))
                block = self._detail_block(meaningful_title or "Evidence document", rows)
                if block.rows:
                    blocks.append(block)
                continue

        return blocks

    def _build_cause_blocks(self, incident: Incident, *, assessment) -> list[IncidentPdfDetailBlock]:
        grouped_causes = defaultdict(list)
        layer_order = {
            IncidentCauseTag.CausalLayer.IMMEDIATE: 0,
            IncidentCauseTag.CausalLayer.ROOT: 1,
        }
        for cause in incident.cause_tags.all().order_by("causal_layer", "id"):
            grouped_causes[self._current_causal_layer_key(cause.causal_layer)].append(cause)

        blocks: list[IncidentPdfDetailBlock] = []
        for layer_key in sorted(grouped_causes, key=lambda key: layer_order.get(key, 99)):
            rows = []
            for cause in grouped_causes[layer_key]:
                rows.append(
                    (
                        f"Cause factor: {self._cause_factor_label(cause.cause_factor)}",
                        "\n".join(
                            [
                                f"Cause: {self._display(cause.cause_option_text)}",
                                f"Reason: {self._display(cause.rationale)}",
                            ]
                        ),
                    )
                )
            block = self._detail_block(self._causal_layer_heading(layer_key), rows)
            if block.rows:
                blocks.append(block)
        return blocks

    def _build_factor_blocks(self, incident: Incident, *, assessment) -> list[IncidentPdfDetailBlock]:
        blocks: list[IncidentPdfDetailBlock] = []
        for safeguard in incident.safeguard_failures.all().order_by("safeguard_name", "id"):
            block = self._detail_block(
                    f"Safeguard failure - {safeguard.safeguard_name}",
                    [
                        ("Safeguard", self._display(safeguard.safeguard_name)),
                        ("Notes", self._display(safeguard.notes)),
                    ],
                )
            if block.rows:
                blocks.append(block)
        return blocks

    def _build_action_blocks_detail(self, recommendations: Iterable[Recommendation]) -> list[IncidentPdfDetailBlock]:
        grouped_rows: dict[str, list[tuple[str, str]]] = {
            Recommendation.Tier.CORRECTIVE: [],
            Recommendation.Tier.PREVENTIVE: [],
        }
        for recommendation in recommendations:
            if recommendation.tier not in grouped_rows:
                continue
            actions = list(recommendation.corrective_actions.all())
            if actions:
                for action in actions:
                    description = self._display(action.description)
                    due_date = self._display(action.due_date)
                    if due_date != "Not recorded":
                        description = f"{description}\nDue Date: {due_date}"
                    grouped_rows[recommendation.tier].append(("", description))
                continue
            grouped_rows[recommendation.tier].append(("", self._display(recommendation.description)))

        blocks: list[IncidentPdfDetailBlock] = []
        for tier, heading in (
            (Recommendation.Tier.CORRECTIVE, "Corrective Actions"),
            (Recommendation.Tier.PREVENTIVE, "Preventive Actions"),
        ):
            block = self._detail_block(heading, grouped_rows[tier])
            if block.rows:
                blocks.append(block)
        return blocks

    def _build_lesson_blocks(self, recommendations: Iterable[Recommendation]) -> list[IncidentPdfDetailBlock]:
        return [
            self._detail_block(
                "Lessons learnt",
                [
                    ("Description", self._display(recommendation.description)),
                    ("Residual risk", self._display(recommendation.residual_risk_statement)),
                ],
            )
            for recommendation in recommendations
            if recommendation.tier == Recommendation.Tier.LESSONS_LEARNT
        ]

    def _build_notification_blocks(self, incident: Incident) -> list[IncidentPdfDetailBlock]:
        blocks: list[IncidentPdfDetailBlock] = []
        office_block = self._detail_block(
            "Office communication",
            [
                ("Office informed?", self._yes_no(incident.office_notified)),
                ("Communication mode", self._choice_label(incident.office_notification_mode)),
            ],
        )
        if office_block.rows:
            blocks.append(office_block)

        history_rows = SafetyFieldHistory.objects.filter(
            parent_table=incident._meta.db_table,
            parent_id=incident.pk,
            field_name__in=[
                "incident_circular_publish",
                "fleet_alert_issue",
                "fleet_alert_notification",
                "phase8_notification",
            ],
        ).order_by("changed_at", "id")
        for row in history_rows:
            block = self._detail_block(
                    "Fleet alert / office notice",
                    [
                        ("Changed at", self._format_pdf_datetime(row.changed_at) or "Not recorded"),
                        ("Details", self._history_text(row.new_value)),
                        ("Reason", self._display(row.change_reason)),
                    ],
                )
            if block.rows:
                blocks.append(block)
        return blocks

    def _build_appendix_blocks(self, incident: Incident) -> list[IncidentPdfDetailBlock]:
        blocks: list[IncidentPdfDetailBlock] = []
        for evidence_item in incident.evidence_items.all().order_by("created_date", "id"):
            attachment_links = self._attachment_links_for_item(incident, evidence_item)
            if not attachment_links:
                continue
            block = self._detail_block(
                    f"Attachment - {evidence_item.title}",
                    [
                        ("Evidence title", self._display(evidence_item.title)),
                        ("File", attachment_links),
                    ],
                )
            if block.rows:
                blocks.append(block)
        return blocks

    def _build_investigator_rows(self, incident: Incident) -> list[tuple[str, str]]:
        phase_log_roles = {(row.actor_role_code or "").upper(): row for row in incident.phase_logs.all()}
        rows = [
            ("Reporter", self._nonblank(incident.reporter_name, incident.reporter_id, default="Not recorded")),
            ("PIC", self._nonblank(incident.pic_user_id, default="Not assigned")),
            ("Master chain evidence", "Present" if "MASTER" in phase_log_roles else "Awaiting phase-log evidence"),
            ("HOD chain evidence", "Present" if "HOD" in phase_log_roles else "Awaiting phase-log evidence"),
            ("Office closer", self._nonblank(incident.dpa_accepted_by, default="Awaiting PIC/DPA signature")),
        ]
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
            (self._causal_layer_label(cause.causal_layer).replace(" Cause", ""), cause.mscat_subcode_id, cause.rationale)
            for cause in incident.cause_tags.all().order_by("id")
        ]
        return rows or [("Root", "Uncoded", "No causal-layer rows recorded.")]

    def _build_causal_factor_points(self, incident: Incident, *, assessment) -> list[str]:
        safeguards = list(incident.safeguard_failures.all())
        evidence_titles = ", ".join(item.title for item in incident.evidence_items.all()[:3]) or "No evidence titles recorded."
        return [
            self._prefixed_point("Describe What happened?", incident.narrative or "Narrative not recorded."),
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
            return ""
        return " ".join(lessons)

    def _build_notification_rows(self, incident: Incident) -> list[tuple[str, str, str]]:
        rows = [
            ("DPA", "Notified" if incident.dpa_notified_at else "Pending", self._format_pdf_datetime(incident.dpa_notified_at) or "N/A"),
            ("FM", "Notified" if incident.fm_notified_at else "Pending", self._format_pdf_datetime(incident.fm_notified_at) or "N/A"),
            ("Office", "Notified" if incident.office_notified_at else "Pending", self._format_pdf_datetime(incident.office_notified_at) or "N/A"),
        ]
        circular_rows = SafetyFieldHistory.objects.filter(
            parent_table=incident._meta.db_table,
            parent_id=incident.pk,
            field_name="incident_circular_publish",
        ).order_by("-changed_at", "-id")
        if circular_rows.exists():
            rows.append(("Fleet Circular", "Published", self._format_pdf_datetime(circular_rows.first().changed_at) or "N/A"))
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
        ]
        office_signature = history_rows.get("phase7_signature_dpa") or history_rows.get("phase7_signature_pic")
        rows.append(self._signature_row("PIC / DPA office signature", row=office_signature))
        return rows

    def _build_appendix_rows(self, incident: Incident) -> list[tuple[str, str, str]]:
        rows: list[tuple[str, str, str]] = []
        for evidence_item in incident.evidence_items.all():
            rows.append((evidence_item.title, evidence_item.item_type, evidence_item.source_label or "Inline evidence"))
        for interview in incident.witness_interviews.all():
            rows.append((interview.witness_name, "Witness interview", interview.interview_type))
        for action in CorrectiveAction.objects.filter(source_table="vims_safety_incident", source_id=incident.pk).order_by("id"):
            rows.append((action.description, "Corrective action", action.status))
        return rows or [("Appendices", "N/A", "No appendix artifacts recorded.")]

    def _reporter_signature_row(self, incident: Incident) -> IncidentPdfSignatureRow:
        return IncidentPdfSignatureRow(
            label="Reporter signature",
            signed_by=self._nonblank(incident.reporter_id, incident.created_by, default=""),
            signed_at=self._format_pdf_datetime(incident.reported_at) or "",
            typed_name=self._nonblank(incident.reporter_name, incident.reporter_id, default=""),
            source_detail="Reporter submission data",
            device_fingerprint=self._display(incident.reporter_device_fingerprint),
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
                "download_path": f"/api/safety/incidents/{incident.id}/pdf/",
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
    def _format_pdf_datetime(value) -> str | None:
        if value is None:
            return None
        if isinstance(value, datetime):
            if timezone.is_aware(value):
                value = timezone.localtime(value)
            return value.strftime("%d %b %Y, %H:%M")
        return str(value)

    @staticmethod
    def _nonblank(*values: str | None, default: str) -> str:
        for value in values:
            if value is not None and str(value).strip():
                return str(value).strip()
        return default

    @staticmethod
    def _display(value, *, default: str = "Not recorded") -> str:
        if value is None:
            return default
        if isinstance(value, str):
            return value.strip() or default
        if isinstance(value, datetime):
            return IncidentPdfRenderer._format_pdf_datetime(value) or default
        return str(value)

    def _vessel_location_text(self, incident: Incident) -> str:
        location = self._display(incident.vessel_location, default="")
        detail = self._display(incident.vessel_location_detail, default="")
        if location and detail:
            return f"{location} - {detail}"
        return location

    @staticmethod
    def _yes_no(value) -> str:
        if value is None:
            return "Not recorded"
        return "Yes" if bool(value) else "No"

    def _position_text(self, incident: Incident) -> str:
        if incident.latitude is None or incident.longitude is None:
            return "Not recorded"
        return f"{incident.latitude}, {incident.longitude}"

    def _json_text(self, value) -> str:
        return self._readable_payload_text(value)

    def _history_text(self, value) -> str:
        if value in (None, "", [], {}):
            return "Not recorded"
        parsed = parse_history_value(value)
        return self._readable_payload_text(parsed) if isinstance(parsed, (dict, list)) else self._display(parsed)

    @staticmethod
    def _humanize_key(value: object) -> str:
        return str(value or "Detail").replace("_", " ").replace("-", " ").strip().title()

    def _choice_label(self, value) -> str:
        text = self._display(value)
        if text == "Not recorded":
            return text
        labels = {
            "ON_CALL": "On call",
            "WHATSAPP": "On WhatsApp",
            "EMAIL": "On email",
            "NOT_APPLICABLE": "Not applicable",
        }
        return labels.get(text, text.replace("_", " ").title())

    def _readable_payload_text(self, value, *, depth: int = 0) -> str:
        if value in (None, "", [], {}):
            return "Not recorded"
        if isinstance(value, str):
            stripped = value.strip()
            if not stripped:
                return "Not recorded"
            try:
                parsed = json.loads(stripped)
            except (TypeError, ValueError):
                return stripped
            return self._readable_payload_text(parsed, depth=depth)
        if isinstance(value, dict):
            parts: list[str] = []
            for key, nested_value in value.items():
                if nested_value in (None, "", [], {}):
                    continue
                label = self._humanize_key(key)
                rendered = self._readable_payload_text(nested_value, depth=depth + 1)
                if rendered != "Not recorded":
                    parts.append(f"{label}: {rendered}")
            return "\n".join(parts) if parts else "Not recorded"
        if isinstance(value, (list, tuple, set)):
            rendered_items = [
                self._readable_payload_text(item, depth=depth + 1)
                for item in value
                if item not in (None, "", [], {})
            ]
            rendered_items = [item for item in rendered_items if item != "Not recorded"]
            if not rendered_items:
                return "Not recorded"
            if all("\n" not in item and len(item) < 80 for item in rendered_items):
                return ", ".join(rendered_items)
            return "\n".join(f"{index}. {item}" for index, item in enumerate(rendered_items, start=1))
        if isinstance(value, bool):
            return self._yes_no(value)
        if isinstance(value, datetime):
            return self._format_pdf_datetime(value) or "Not recorded"
        return str(value)

    def _extract_attachment_paths(self, value, *, key_hint: str = "") -> list[str]:
        if isinstance(value, dict):
            paths: list[str] = []
            for key, nested_value in value.items():
                paths.extend(self._extract_attachment_paths(nested_value, key_hint=str(key)))
            return paths
        if isinstance(value, list):
            paths: list[str] = []
            for nested_value in value:
                paths.extend(self._extract_attachment_paths(nested_value, key_hint=key_hint))
            return paths
        if not isinstance(value, str):
            return []

        key = key_hint.lower()
        if key and not any(token in key for token in ("attachment", "path", "file", "photo", "scan", "evidence")):
            return []
        candidate = value.strip()
        if not candidate:
            return []
        suffix = Path(candidate).suffix.lower()
        if suffix not in ATTACHMENT_FILE_SUFFIXES:
            return []
        return [candidate]

    def _attachment_links_from_metadata(self, incident: Incident, metadata_value) -> str:
        metadata = metadata_value if isinstance(metadata_value, dict) else {}
        links: list[str] = []
        seen_labels: set[str] = set()
        seen_paths: set[str] = set()
        for path in self._extract_attachment_paths(metadata):
            path_text = str(path).strip()
            path_key = path_text.replace("\\", "/").casefold()
            if not path_key or path_key in seen_paths:
                continue
            label = self._attachment_label(metadata, path_text)
            label_key = str(label).strip().casefold()
            if label_key and label_key in seen_labels:
                continue
            seen_paths.add(path_key)
            if label_key:
                seen_labels.add(label_key)
            href = f"/api/safety/incidents/{incident.id}/phase-4/evidence/attachments/?path={quote(path_text, safe='')}"
            links.append(f"PDF_LINK::{href}::{label}")
        return "\n".join(links)

    def _attachment_links_for_item(self, incident: Incident, item) -> str:
        return self._attachment_links_from_metadata(incident, item.metadata_json)

    def _witness_statement_attachment_link(self, incident: Incident, interview: WitnessInterview) -> str:
        if not self._witness_statement_attachment_is_downloadable(interview.witness_signature):
            return "Not recorded"
        href = f"/api/safety/incidents/{incident.id}/phase-4/interviews/{interview.id}/statement-attachment/"
        return f"PDF_LINK::{href}::Witness statement attachment"

    @staticmethod
    def _witness_statement_attachment_is_downloadable(value) -> bool:
        text = str(value or "").strip()
        return text.startswith("data:") and ";base64," in text

    def _attachment_label(self, metadata: dict, path: str) -> str:
        direct_label = str(metadata.get("original_name") or metadata.get("file_name") or "").strip()
        if direct_label:
            return direct_label
        for attachment in metadata.get("attachments") or []:
            if not isinstance(attachment, dict):
                continue
            attachment_path = str(attachment.get("attachment_path") or "").strip()
            if attachment_path != str(path).strip():
                continue
            label = str(attachment.get("original_name") or attachment.get("file_name") or "").strip()
            if label:
                return label
        return Path(str(path)).name

    @staticmethod
    def _clean_text(value) -> str:
        if value is None:
            return ""
        return str(value).strip()

    @classmethod
    def _meaningful_evidence_title(cls, title: str, attachment_links: str) -> str:
        title_text = cls._clean_text(title)
        if not title_text:
            return ""
        title_name = Path(title_text).name.casefold()
        for label in cls._attachment_link_labels(attachment_links):
            if title_name == Path(label).name.casefold():
                return ""
        if cls._looks_like_generated_attachment_title(title_text):
            return ""
        return title_text

    @staticmethod
    def _attachment_link_labels(attachment_links: str) -> list[str]:
        labels: list[str] = []
        for line in str(attachment_links or "").splitlines():
            if not line.startswith("PDF_LINK::"):
                continue
            parts = line.split("::", 2)
            if len(parts) == 3 and parts[2].strip():
                labels.append(parts[2].strip())
        return labels

    @staticmethod
    def _looks_like_generated_attachment_title(value: str) -> bool:
        file_name = Path(str(value or "").strip()).name
        if not file_name or " " in file_name:
            return False
        suffix = Path(file_name).suffix.lower()
        if suffix not in ATTACHMENT_FILE_SUFFIXES:
            return False
        stem = Path(file_name).stem
        return len(stem) > 24 or any(character.isdigit() for character in stem)

    @staticmethod
    def _evidence_tab_label(value) -> str:
        labels = {
            "POSITION": "Position / scene",
            "PEOPLE": "People / witness",
            "PARTS": "Parts / equipment",
            "PAPER": "Documents",
            "ELECTRONIC": "Electronic records",
        }
        text = str(value or "").strip().upper()
        return labels.get(text, text.replace("_", " ").title() or "Evidence")

    @staticmethod
    def _mscat_subcode_label(value) -> str:
        if value in (None, ""):
            return "Not recorded"
        try:
            row = MasterMscatTaxonomy.objects.filter(subcode_id=str(value)).first()
        except DatabaseError:
            return str(value)
        if row is None:
            return str(value)
        return " - ".join(part for part in [row.category_name, row.subcode_description, row.subcode_id] if part)

    @staticmethod
    def _cause_factor_label(value) -> str:
        labels = {
            "HUMAN": "Human",
            "VESSEL": "Vessel",
            "MANAGEMENT": "Management",
            "OTHER": "Other",
        }
        if value in (None, ""):
            return "Not recorded"
        return labels.get(str(value).strip().upper(), str(value).replace("_", " ").title())

    @staticmethod
    def _causal_layer_label(value) -> str:
        labels = {
            IncidentCauseTag.CausalLayer.IMMEDIATE: "Immediate Cause",
            IncidentCauseTag.CausalLayer.ROOT: "Root Cause",
        }
        if value in (None, ""):
            return "Not recorded"
        return labels.get(IncidentPdfRenderer._current_causal_layer_key(value), "Root Cause")

    @classmethod
    def _causal_layer_heading(cls, value) -> str:
        return cls._causal_layer_label(value)

    @staticmethod
    def _current_causal_layer_key(value) -> str:
        text = str(value or "").strip().upper()
        if text == IncidentCauseTag.CausalLayer.IMMEDIATE:
            return IncidentCauseTag.CausalLayer.IMMEDIATE
        return IncidentCauseTag.CausalLayer.ROOT

    @staticmethod
    def _incident_type_name(value) -> str:
        if value in (None, ""):
            return "Not recorded"
        row = (
            MasterSafetyIncidentType.objects.filter(legacy_int_id=value).first()
            or MasterSafetyIncidentType.objects.filter(type_code=str(value)).first()
        )
        if row is None:
            return str(value)
        return row.type_name or str(value)

    @staticmethod
    def _loss_type_name(value) -> str:
        if value in (None, ""):
            return "Not recorded"
        row = MasterLossType.objects.filter(loss_type_id=value).first()
        if row is None:
            return str(value)
        return row.loss_type_name or str(value)

    @staticmethod
    def _weather_option_label(value) -> str:
        if value in (None, ""):
            return "Not recorded"
        value_text = str(value)
        try:
            row = IncidentWeatherOption.objects.filter(pk=value).first()
        except (DatabaseError, ValueError, TypeError):
            row = None
        if row is not None:
            return row.option_label or value_text

        fallback_prefix = "00000000-0000-4000-8000-"
        if value_text.startswith(fallback_prefix):
            try:
                fallback_index = int(value_text.removeprefix(fallback_prefix), 16) - 1
            except ValueError:
                fallback_index = -1
            if 0 <= fallback_index < len(WEATHER_OPTION_SEEDS):
                return WEATHER_OPTION_SEEDS[fallback_index][1]
        normalized_value_text = value_text.replace("-", "").lower()
        fallback_prefix_char32 = "00000000000040008000"
        if normalized_value_text.startswith(fallback_prefix_char32):
            try:
                fallback_index = int(normalized_value_text.removeprefix(fallback_prefix_char32), 16) - 1
            except ValueError:
                fallback_index = -1
            if 0 <= fallback_index < len(WEATHER_OPTION_SEEDS):
                return WEATHER_OPTION_SEEDS[fallback_index][1]
        return value_text

    @staticmethod
    def _join_nonblank(*values: object) -> str:
        parts = [str(value).strip() for value in values if value is not None and str(value).strip()]
        return "\n".join(parts)

    @staticmethod
    def _detail_block(heading: str, rows: list[tuple[str, str]]) -> IncidentPdfDetailBlock:
        skip_values = {
            "",
            "N/A",
            "Not closed",
            "Not recorded",
            "No data recorded.",
            "No evidence rows recorded.",
            "No recommendation rows recorded.",
            "Timeline/status not recorded.",
        }

        def _row_value(value) -> str:
            if value is None:
                return ""
            value_text = str(value).strip()
            return value_text

        cleaned_rows = []
        for label, value in rows:
            value_text = _row_value(value)
            if value_text in skip_values:
                continue
            cleaned_rows.append(("", value_text) if str(label).strip() == "" else (str(label), value_text))
        return IncidentPdfDetailBlock(
            heading=str(heading or "Detail"),
            rows=cleaned_rows,
        )

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
                signed_at=self._format_pdf_datetime(row.occurred_at),
                signed_by=row.actor_user_id,
                typed_name=row.actor_user_id,
                source_detail=f"Phase log; signature valid: {self._yes_no(row.signature_valid)}",
                device_fingerprint=row.device_fingerprint,
            )

        payload = {}
        if getattr(row, "new_value", None):
            parsed = parse_history_value(row.new_value)
            if isinstance(parsed, dict):
                payload = parsed
        return IncidentPdfSignatureRow(
            label=label,
            signed_at=str(payload.get("signed_at") or self._format_pdf_datetime(getattr(row, "changed_at", None)) or ""),
            signed_by=str(payload.get("signed_by") or getattr(row, "actor_user_id", "") or ""),
            typed_name=str(payload.get("typed_name") or payload.get("signed_by") or ""),
            source_detail=f"Field history: {getattr(row, 'field_name', 'signature')}",
            device_fingerprint=str(payload.get("device_fingerprint") or "Not recorded"),
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
        incident_id,
        viewer_user,
        persist: bool = True,
    ) -> NearMissPdfRenderResult:
        near_miss = self._get_near_miss(incident_id)
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
            download_path=f"/api/safety/near-miss/{near_miss.id}/pdf/",
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
        viewer_visible = True
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
            place=self._format_near_miss_place(near_miss.near_miss_place),
            categories=self._format_list(serialized.get("near_miss_category_tags"), near_miss.near_miss_shell_tag, default="Not selected"),
            near_miss_types=self._build_near_miss_type_text(near_miss, serialized=serialized),
            possible_loss_type=self._build_loss_type_text(near_miss),
            cause_factor_rows=self._build_near_miss_cause_factor_rows(serialized),
            occurred_at=self._format_pdf_datetime(near_miss.occurred_at),
            reported_at=self._format_pdf_datetime(near_miss.reported_at),
            reporter_name=self._nonblank(serialized.get("reporter_name"), default=""),
            reporter_rank=self._nonblank(serialized.get("reporter_rank"), default=""),
            what_happened=self._nonblank(serialized.get("narrative"), default=""),
            suggestion_text=self._build_suggestion_text(near_miss, suggestion),
            immediate_action_text=self._build_immediate_action_text(near_miss),
            root_cause_detail=self._nonblank(near_miss.near_miss_root_cause_detail, default=""),
            corrective_action=self._nonblank(near_miss.near_miss_corrective_action, default=""),
            weather_voyage_details=self._nonblank(near_miss.near_miss_weather_voyage_details, default=""),
            equipment_details=self._nonblank(near_miss.near_miss_equipment_details, default=""),
            lessons_learned=self._nonblank(near_miss.near_miss_lessons_learned, default=""),
            vessel_review_comment=self._build_vessel_review_comment_text(near_miss, serialized=serialized),
            office_comments=self._build_office_comment_text(near_miss),
            closure_reason=self._nonblank(near_miss.closure_reason, default=""),
            fleet_alert_issued_at=self._format_pdf_datetime(getattr(fleet_status, "issued_at", None)),
            fleet_learning_text=self._nonblank(fleet_learning, default=""),
            generated_at=self._format_pdf_datetime(timezone.now()) or "",
            visibility_note=(
                "Reporter details are visible to authorized users."
                if viewer_visible
                else ""
            ),
            signature_rows=self._build_signature_rows(near_miss),
        )

    @staticmethod
    def _build_immediate_action_text(near_miss: Incident) -> str:
        if (near_miss.near_miss_immediate_action or "").strip():
            return near_miss.near_miss_immediate_action.strip()
        return ""

    @staticmethod
    def _build_suggestion_text(near_miss: Incident, suggestion: dict[str, str]) -> str:
        if (near_miss.near_miss_suggestion or "").strip():
            return near_miss.near_miss_suggestion.strip()
        return ""

    @staticmethod
    def _format_near_miss_place(value: str | None) -> str:
        labels = {
            "AT_ANCHOR": "At Anchor",
            "AT_SEA": "At Sea",
            "AT_PORT": "At Port",
        }
        return labels.get(str(value or "").strip().upper(), "Not selected")

    @staticmethod
    def _format_list(values, fallback: object | None = None, *, default: str = "Not selected") -> str:
        cleaned: list[str] = []
        if isinstance(values, list):
            cleaned = [str(value).strip() for value in values if str(value or "").strip()]
        fallback_text = str(fallback or "").strip()
        if fallback_text and fallback_text not in cleaned:
            cleaned.append(fallback_text)
        return ", ".join(cleaned) if cleaned else default

    def _build_near_miss_type_text(self, near_miss: Incident, *, serialized: dict) -> str:
        type_ids = self._coerce_int_list(serialized.get("near_miss_incident_type_ids"))
        if near_miss.incident_type_id and near_miss.incident_type_id not in type_ids:
            type_ids.insert(0, int(near_miss.incident_type_id))
        if not type_ids:
            return "Not selected"

        label_by_id: dict[int, str] = {}
        try:
            rows = MasterSafetyIncidentType.objects.filter(legacy_int_id__in=type_ids)
            label_by_id = {int(row.legacy_int_id): row.type_name for row in rows}
        except Exception:
            label_by_id = {}
        return ", ".join(label_by_id.get(type_id, f"Type {type_id}") for type_id in type_ids)

    @staticmethod
    def _build_loss_type_text(near_miss: Incident) -> str:
        if not near_miss.loss_type_primary_id:
            return "Not selected"
        try:
            row = MasterLossType.objects.filter(loss_type_id=near_miss.loss_type_primary_id).first()
        except Exception:
            row = None
        return row.loss_type_name if row is not None else f"Loss type {near_miss.loss_type_primary_id}"

    def _build_immediate_cause_text(self, near_miss: Incident, *, serialized: dict) -> str:
        factor_causes = self._coerce_factor_causes(serialized.get("near_miss_factor_causes"))
        if factor_causes:
            lines: list[str] = []
            factor_labels = {
                "HUMAN": "Human Factors",
                "VESSEL": "Vessel Factors",
                "MANAGEMENT": "Management Factors",
                "OTHER": "Other Factors",
            }
            for row in factor_causes:
                factor = factor_labels.get(str(row.get("factor") or "").strip().upper(), "Factor")
                immediate = self._factor_cause_label(row, "immediate")
                root = self._factor_cause_label(row, "root")
                lines.append(f"{factor}: Immediate - {immediate}; Root - {root}")
            return "\n".join(lines)

        subcodes = self._coerce_text_list(serialized.get("near_miss_mscat_subcode_ids"))
        fallback = str(near_miss.near_miss_mscat_subcode_id or "").strip()
        if fallback and fallback not in subcodes:
            subcodes.insert(0, fallback)
        if not subcodes:
            other_detail = str(near_miss.near_miss_root_cause_detail or "").strip()
            return other_detail or "Not selected"

        label_by_subcode: dict[str, str] = {}
        try:
            rows = MasterMscatTaxonomy.objects.filter(subcode_id__in=subcodes)
            label_by_subcode = {
                row.subcode_id: f"{row.subcode_id} - {row.subcode_description}"
                for row in rows
            }
        except Exception:
            label_by_subcode = {}
        return "; ".join(label_by_subcode.get(subcode, subcode) for subcode in subcodes)

    def _build_near_miss_cause_factor_rows(self, serialized: dict) -> list[NearMissCauseFactorPdfRow]:
        factor_causes = self._coerce_factor_causes(serialized.get("near_miss_factor_causes"))
        if not factor_causes:
            return []

        factor_labels = {
            "HUMAN": "Human Factors",
            "VESSEL": "Vessel Factors",
            "MANAGEMENT": "Management Factors",
            "OTHER": "Other Factors",
        }
        order = ["HUMAN", "VESSEL", "MANAGEMENT", "OTHER"]
        row_by_factor = {
            str(row.get("factor") or "").strip().upper(): row
            for row in factor_causes
            if isinstance(row, dict)
        }

        rows: list[NearMissCauseFactorPdfRow] = []
        for factor in order:
            row = row_by_factor.get(factor)
            if not row:
                continue
            rows.append(
                NearMissCauseFactorPdfRow(
                    factor=factor_labels[factor],
                    immediate_cause=self._factor_cause_label(row, "immediate"),
                    root_cause=self._factor_cause_label(row, "root"),
                )
            )
        return rows

    @staticmethod
    def _coerce_factor_causes(value) -> list[dict]:
        if isinstance(value, list):
            return [row for row in value if isinstance(row, dict)]
        if isinstance(value, str) and value.strip():
            try:
                parsed = json.loads(value)
            except (TypeError, ValueError):
                return []
            if isinstance(parsed, list):
                return [row for row in parsed if isinstance(row, dict)]
        return []

    @staticmethod
    def _factor_cause_label(row: dict, stage: str) -> str:
        option_text = str(row.get(f"{stage}_option_text") or "").strip()
        other_text = str(row.get(f"{stage}_other_text") or "").strip()
        if option_text.lower() in {"other", "others", "other-specify"} and other_text:
            return other_text
        return option_text or other_text or "Not selected"

    @staticmethod
    def _build_office_comment_text(near_miss: Incident) -> str:
        row = (
            near_miss.phase_logs.filter(
                transition_type=IncidentPhaseLog.TransitionType.FORWARD,
                actor_role_code__in=["DPA", "PIC", "OFFICE_PIC", "OFFICE_SSQE", "OFFICE_SUPT", "VESSEL SUPERINTENDENT"],
            )
            .order_by("-occurred_at", "-id")
            .first()
        )
        if row and str(row.loop_back_reason or "").strip():
            return NearMissLightweightPdfRenderer._strip_office_comment_prefix(str(row.loop_back_reason).strip())
        return "Not recorded."

    @staticmethod
    def _build_vessel_review_comment_text(near_miss: Incident, *, serialized: dict) -> str:
        vessel_review_summary = serialized.get("vessel_review_summary")
        if isinstance(vessel_review_summary, dict) and str(vessel_review_summary.get("comment") or "").strip():
            return str(vessel_review_summary["comment"]).strip()

        row = (
            SafetyFieldHistory.objects.filter(
                parent_table=near_miss._meta.db_table,
                parent_id=near_miss.pk,
                field_name="near_miss_vessel_review_signature",
            )
            .order_by("-changed_at", "-id")
            .first()
        )
        if row is not None and str(row.change_reason or "").strip():
            payload = parse_history_value(row.new_value)
            decision = ""
            if isinstance(payload, dict):
                decision = str(payload.get("decision") or "").strip()
            fallback = f"Near-miss vessel review decision: {decision}."
            comment = str(row.change_reason).strip()
            if comment != fallback:
                return comment
        return "Not recorded."

    @staticmethod
    def _strip_office_comment_prefix(value: str) -> str:
        prefixes = ("Office comment:", "Office comments:")
        for prefix in prefixes:
            if value.lower().startswith(prefix.lower()):
                return value[len(prefix):].strip() or value
        return value

    @staticmethod
    def _build_rework_summary_text(near_miss: Incident, *, serialized: dict) -> str:
        rework_summary = serialized.get("rework_summary")
        if isinstance(rework_summary, dict) and str(rework_summary.get("comment") or "").strip():
            return str(rework_summary["comment"]).strip()

        row = (
            SafetyFieldHistory.objects.filter(
                parent_table=near_miss._meta.db_table,
                parent_id=near_miss.pk,
                field_name="near_miss_rework_resubmission",
            )
            .order_by("-changed_at", "-id")
            .first()
        )
        if row is not None:
            payload = parse_history_value(row.new_value)
            if isinstance(payload, dict) and str(payload.get("comment") or "").strip():
                return str(payload["comment"]).strip()
            if str(row.change_reason or "").strip():
                return str(row.change_reason).strip()
        return "Not recorded."

    @staticmethod
    def _coerce_text_list(values) -> list[str]:
        if not isinstance(values, list):
            return []
        cleaned: list[str] = []
        for value in values:
            text = str(value or "").strip()
            if text and text not in cleaned:
                cleaned.append(text)
        return cleaned[:3]

    def _coerce_int_list(self, values) -> list[int]:
        cleaned: list[int] = []
        for value in self._coerce_text_list(values):
            try:
                numeric = int(value)
            except (TypeError, ValueError):
                continue
            if numeric not in cleaned:
                cleaned.append(numeric)
        return cleaned[:3]

    @staticmethod
    def _format_pdf_datetime(value) -> str | None:
        if value is None:
            return None
        parsed = value
        if isinstance(value, str):
            cleaned = value.strip()
            if not cleaned:
                return None
            try:
                parsed = datetime.fromisoformat(cleaned.replace("Z", "+00:00"))
            except ValueError:
                return cleaned
        if isinstance(parsed, datetime):
            if timezone.is_aware(parsed):
                parsed = timezone.localtime(parsed)
            return parsed.strftime("%d %b %Y, %H:%M")
        return str(parsed)

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
                    label="Office review signature",
                    signed_at=self._format_pdf_datetime(triage_log.occurred_at),
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
        return rows

    def _field_history_signature_row(self, label: str, *, row) -> NearMissPdfSignatureRow:
        payload = {}
        if getattr(row, "new_value", None):
            parsed = parse_history_value(row.new_value)
            if isinstance(parsed, dict):
                payload = parsed

        return NearMissPdfSignatureRow(
            label=label,
            signed_at=self._format_pdf_datetime(payload.get("signed_at") or getattr(row, "changed_at", None)) or "Awaiting signature",
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
                "download_path": f"/api/safety/near-miss/{near_miss.id}/pdf/",
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
        meeting_id,
        viewer_user,
        persist: bool = True,
    ) -> SCMPdfRenderResult:
        meeting = self._get_meeting(meeting_id)
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
            download_path=f"/api/safety/scm/{meeting.id}/pdf/",
            export_path=export_path,
            file_name=self._build_file_name(meeting),
            meeting_id=meeting.pk,
            section_titles=[f"{row.agenda_item_number}. {row.section_label}" for row in context.section_rows],
        )

    def _get_meeting(self, meeting_id: int) -> SCMMeeting:
        return self.repository.read(meeting_id)

    @staticmethod
    def _validate_exportable(meeting: SCMMeeting) -> None:
        if meeting.is_deleted:
            raise ValidationError("Deleted SCM meetings cannot be exported.")

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
            section_rows=section_rows,
        )

    def _build_section_rows(self, meeting: SCMMeeting) -> list[SCMLegacySectionRow]:
        agenda_rows = list(self.repository.list_sections(meeting.id))
        legacy_map = self._build_legacy_field_map(meeting.id)
        if (meeting.office_comment or "").strip():
            legacy_map.setdefault(9, {})["officecomments"] = meeting.office_comment.strip()
        if getattr(meeting, "office_comment_at", None) is not None or (meeting.office_comment or "").strip():
            legacy_map.setdefault(9, {})["isreviewed"] = True
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

        agenda_map = {int(row.agenda_item_number): row for row in agenda_rows}
        legacy_source_map = {1: 1, 2: 3, 3: 4, 4: 5, 5: 6, 6: 7, 7: 8, 8: 9, 9: 10}
        section_rows: list[SCMLegacySectionRow] = []
        for template_row in build_default_scm_sections():
            section_number = int(template_row["agenda_item_number"])
            legacy_source_number = legacy_source_map.get(section_number, section_number)
            agenda_row = self._select_section_row(
                agenda_map,
                section_number=section_number,
                legacy_source_number=legacy_source_number,
            )
            current_legacy_fields = legacy_map.get(section_number, {})
            legacy_source_fields = legacy_map.get(legacy_source_number, {})
            selected_legacy_fields = (
                current_legacy_fields
                if self._has_nonblank_legacy_values(current_legacy_fields)
                else legacy_source_fields
            )
            section_rows.append(
                SCMLegacySectionRow(
                    agenda_item_number=section_number,
                    section_label=str(template_row["section_label"]),
                    content=(
                        (getattr(agenda_row, "content", None) or "").strip()
                        if agenda_row is not None
                        else "No section content recorded."
                    )
                    or "No section content recorded.",
                    decision=(
                        (getattr(agenda_row, "decision", None) or "").strip()
                        if agenda_row is not None
                        else None
                    )
                    or None,
                    legacy_fields={
                        **_blank_legacy_fields(section_number),
                        **selected_legacy_fields,
                    },
                )
            )
        return section_rows

    @staticmethod
    def _select_section_row(
        agenda_map: dict[int, object],
        *,
        section_number: int,
        legacy_source_number: int,
    ):
        current_row = agenda_map.get(section_number)
        legacy_row = agenda_map.get(legacy_source_number)
        if current_row is None:
            return legacy_row
        current_label = str(getattr(current_row, "section_label", "") or "").strip().lower()
        if section_number == 2 and current_label == "reserved":
            return legacy_row or current_row
        return current_row

    @staticmethod
    def _has_nonblank_legacy_values(values: dict[str, object]) -> bool:
        return any(value not in (None, "") and str(value).strip() for value in values.values())

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
                absence_reason=(str(row.get("absence_reason") or "").strip() or None),
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
                "empty_message": "Closed-since-last SCM data is unavailable.",
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
                "empty_message": "Closed-since-last SCM data could not be rendered.",
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
                "download_path": f"/api/safety/scm/{meeting.id}/pdf/",
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
        inspection_id,
        viewer_user,
        persist: bool = True,
    ) -> SOISummaryPdfRenderResult:
        inspection = self._get_inspection(inspection_id)
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
            download_path=f"/api/safety/soi/{inspection.id}/pdf/",
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
                "download_path": f"/api/safety/soi/{inspection.id}/pdf/",
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
    incident_id: object
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
        incident_id,
        viewer_user,
        persist: bool = True,
    ) -> MscMepc3PdfRenderResult:
        incident = self._get_incident(incident_id)
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
            download_path=f"/api/safety/export/msc-mepc-3/{incident.id}/",
            export_path=export_path,
            file_name=self._build_file_name(incident),
            incident_id=incident.pk,
            appendix_titles=list(self.template.APPENDIX_TITLES),
        )

    def _get_incident(self, incident_id) -> Incident:
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
                "Field 08 - Marine documents checklist",
                "Complete" if incident.marine_docs_checklist_done else "Pending",
                "vims_safety_incident.marine_docs_checklist_done",
            ),
            (
                "Field 09 - Chain of custody status",
                "Complete" if incident.chain_of_custody_ok else "Pending",
                "vims_safety_incident.chain_of_custody_ok",
            ),
            (
                "Field 10 - Cargo evidence applicable",
                "Yes" if incident.cargo_evidence_applicable else "No",
                "vims_safety_incident.cargo_evidence_applicable",
            ),
            (
                "Field 11 - Health / fatigue applicable",
                "Yes" if incident.health_fatigue_applicable else "No",
                "vims_safety_incident.health_fatigue_applicable",
            ),
            (
                "Field 12 - Causal layering complete",
                "Yes" if incident.causal_layering_complete else "No",
                "vims_safety_incident.causal_layering_complete",
            ),
            (
                "Field 13 - ALARP attested",
                "Yes" if incident.alarp_attested else "No",
                "vims_safety_incident.alarp_attested",
            ),
            (
                "Field 14 - Bias guard attestations",
                incident.bias_guard_attestations or "Not recorded",
                "vims_safety_incident.bias_guard_attestations",
            ),
            (
                "Field 15 - Reporter rank",
                self._string_value(incident.reporter_rank, default="Not recorded"),
                "vims_safety_incident.reporter_rank",
            ),
            (
                "Field 16 - Reporter department",
                self._string_value(incident.reporter_department, default="Not recorded"),
                "vims_safety_incident.reporter_department",
            ),
            (
                "Field 17 - DPA notified",
                self._string_value(self._serialize_datetime(incident.dpa_notified_at), default="Not recorded"),
                "vims_safety_incident.dpa_notified_at",
            ),
            (
                "Field 18 - FM notified",
                self._string_value(self._serialize_datetime(incident.fm_notified_at), default="Not recorded"),
                "vims_safety_incident.fm_notified_at",
            ),
            (
                "Field 19 - Office notified",
                self._string_value(self._serialize_datetime(incident.office_notified_at), default="Not recorded"),
                "vims_safety_incident.office_notified_at",
            ),
            (
                "Field 20 - Vessel flag",
                self._string_value(vessel_particulars.get("flags"), default="Not available in workspace"),
                "VesselData.flags",
            ),
            (
                "Field 21 - Vessel class",
                self._string_value(vessel_particulars.get("ClassificationSociety"), default="Not available in workspace"),
                "VesselData.ClassificationSociety",
            ),
            (
                "Field 22 - Vessel gross tonnage",
                self._string_value(vessel_particulars.get("grt"), default="Not available in workspace"),
                "VesselData.grt",
            ),
            (
                "Field 23 - Vessel deadweight",
                self._string_value(vessel_particulars.get("deadweight"), default="Not available in workspace"),
                "VesselData.deadweight",
            ),
            (
                "Field 24 - Cargo quantity",
                self._string_value(reporting_context.get("total_cargo_weight"), default="Not available"),
                f"{reporting_context.get('source_table') or 'Daily Report'}.TotalCargoWeight",
            ),
            (
                "Field 25 - Voyage condition",
                self._string_value(reporting_context.get("voy_condition"), default="Not available"),
                f"{reporting_context.get('source_table') or 'Daily Report'}.VoyCondition",
            ),
            (
                "Field 26 - Weather remarks",
                self._string_value(reporting_context.get("weather_remarks"), default="Not available"),
                f"{reporting_context.get('source_table') or 'Daily Report'}.WeatherRemarks",
            ),
            (
                "Field 27 - Wind force",
                self._string_value(reporting_context.get("wind_force"), default="Not available"),
                f"{reporting_context.get('source_table') or 'Daily Report'}.WindForce",
            ),
            (
                "Field 28 - Sea state",
                self._string_value(reporting_context.get("sea_state"), default="Not available"),
                f"{reporting_context.get('source_table') or 'Daily Report'}.SeaState",
            ),
            (
                "Field 29 - Current strength",
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
                "download_path": f"/api/safety/export/msc-mepc-3/{incident.id}/",
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
