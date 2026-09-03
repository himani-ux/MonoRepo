"""Serializers for Audit detail and scorecard endpoints."""

from __future__ import annotations

from rest_framework import serializers

from apps.inspection.audit.finding_types import is_nc_finding, is_observation_finding
from apps.inspection.audit.services.detail import AuditDetailBundle, valid_audit_area_codes


VERIFY_CHOICES = ("YES", "NO", "NA")
SCORECARD_STATUS_CHOICES = ("SATISFACTORY", "NEEDS_IMPROVEMENT", "NC_RAISED", "N_A")


class AuditDetailPatchSerializer(serializers.Serializer):
    audit_scope = serializers.CharField(required=False, allow_blank=True)
    terms_of_reference = serializers.CharField(required=False, allow_blank=True)
    audit_summary = serializers.CharField(required=False, allow_blank=True)
    equipment_tested = serializers.CharField(required=False, allow_blank=True)
    opening_meeting_at = serializers.DateTimeField(required=False, allow_null=True)
    closing_meeting_at = serializers.DateTimeField(required=False, allow_null=True)
    prev_internal_ca_verified = serializers.ChoiceField(choices=VERIFY_CHOICES, required=False, allow_blank=True)
    prev_external_ca_verified = serializers.ChoiceField(choices=VERIFY_CHOICES, required=False, allow_blank=True)

    def validate(self, data):
        opening = data.get("opening_meeting_at")
        closing = data.get("closing_meeting_at")
        current = self.context.get("audit_detail")
        if current is not None:
            opening = opening if "opening_meeting_at" in data else current.opening_meeting_at
            closing = closing if "closing_meeting_at" in data else current.closing_meeting_at
        if opening and closing and closing < opening:
            raise serializers.ValidationError({"closing_meeting_at": "Closing meeting cannot be before opening meeting."})
        return data


class AuditScorecardRowSerializer(serializers.Serializer):
    area_code = serializers.CharField(max_length=40)
    status = serializers.ChoiceField(choices=SCORECARD_STATUS_CHOICES)
    remarks = serializers.CharField(required=False, allow_blank=True)


class AuditScorecardSerializer(serializers.Serializer):
    rows = AuditScorecardRowSerializer(many=True)

    def validate_rows(self, value):
        area_codes = [row["area_code"] for row in value]
        if len(area_codes) != len(set(area_codes)):
            raise serializers.ValidationError("Scorecard rows cannot contain duplicate area_code values.")

        valid_codes = valid_audit_area_codes()
        unknown_codes = sorted(set(area_codes) - valid_codes)
        if unknown_codes:
            raise serializers.ValidationError({"area_code": f"Unknown audit area code(s): {', '.join(unknown_codes)}"})
        return value


class AuditDetailResponseSerializer(serializers.Serializer):
    def to_representation(self, instance: AuditDetailBundle):
        audit_detail = instance.audit_detail
        inspection = instance.inspection
        nc_count = sum(1 for finding in instance.findings if is_nc_finding(finding["finding_type"]))
        observation_count = sum(1 for finding in instance.findings if is_observation_finding(finding["finding_type"]))

        return {
            "id": str(audit_detail.id),
            "inspection_id": str(inspection.id),
            "inspection": {
                "id": str(inspection.id),
                "vessel_id": str(inspection.vessel_id),
                "inspection_date": inspection.inspection_date.isoformat(),
                "port_place": inspection.port_place,
                "country": inspection.country or "",
                "authority": inspection.authority or "",
                "inspector_name": inspection.inspector_name or "",
                "report_reference": inspection.report_reference or "",
            },
            "audit_classification": audit_detail.audit_classification,
            "auditee_type": audit_detail.auditee_type,
            "auditee_office_dept": audit_detail.auditee_office_dept,
            "audit_subtype": audit_detail.audit_subtype,
            "lead_auditor_name": audit_detail.lead_auditor_name,
            "lead_auditor_designation": audit_detail.lead_auditor_designation,
            "lead_auditor_company": audit_detail.lead_auditor_company,
            "lead_auditor_qual": audit_detail.lead_auditor_qual,
            "trigger_reason": audit_detail.trigger_reason,
            "audit_start_date": audit_detail.audit_start_date.isoformat(),
            "audit_end_date": audit_detail.audit_end_date.isoformat() if audit_detail.audit_end_date else None,
            "opening_meeting_at": audit_detail.opening_meeting_at.isoformat() if audit_detail.opening_meeting_at else None,
            "closing_meeting_at": audit_detail.closing_meeting_at.isoformat() if audit_detail.closing_meeting_at else None,
            "audit_scope": audit_detail.audit_scope or "",
            "terms_of_reference": audit_detail.terms_of_reference or "",
            "audit_summary": audit_detail.audit_summary or "",
            "equipment_tested": audit_detail.equipment_tested or "",
            "prev_internal_ca_verified": audit_detail.prev_internal_ca_verified or "",
            "prev_external_ca_verified": audit_detail.prev_external_ca_verified or "",
            "status": audit_detail.status,
            "external_audit_subtypes": [
                value.strip()
                for value in str(audit_detail.external_audit_subtypes_csv or "").split(",")
                if value.strip()
            ],
            "external_audit_org_id": str(audit_detail.external_audit_org_id) if audit_detail.external_audit_org_id else None,
            "external_audit_org_type": audit_detail.external_audit_org_type or "",
            "external_lead_auditor_name": audit_detail.external_lead_auditor_name or "",
            "external_lead_auditor_credential": audit_detail.external_lead_auditor_credential or "",
            "flag_state_code": audit_detail.flag_state_code or "",
            "cycle_year": audit_detail.cycle_year,
            "linked_cert_ids": [
                value.strip()
                for value in str(audit_detail.linked_cert_ids_csv or "").split(",")
                if value.strip()
            ],
            "certificate_impact": audit_detail.certificate_impact or "",
            "external_closure_status": audit_detail.external_closure_status or "",
            "is_cycle_resetting": audit_detail.is_cycle_resetting,
            "cycle_reset_reason": audit_detail.cycle_reset_reason or "",
            "standards": [standard.standard_code for standard in instance.standards],
            "team_members": [
                {
                    "id": str(member.id),
                    "member_name": member.member_name,
                    "member_designation": member.member_designation or "",
                    "member_company": member.member_company or "",
                    "member_role": member.member_role or "",
                    "sequence_no": member.sequence_no,
                }
                for member in instance.team_members
            ],
            "attendees": [
                {
                    "id": str(attendee.id),
                    "attendee_name": attendee.attendee_name,
                    "attendee_rank": attendee.attendee_rank or "",
                    "opening_present": attendee.opening_present,
                    "closing_present": attendee.closing_present,
                    "sequence_no": attendee.sequence_no,
                }
                for attendee in instance.attendees
            ],
            "counts": {
                "nc": nc_count,
                "observations": observation_count,
                "total_findings": len(instance.findings),
            },
            "scorecard": [
                {
                    "area_code": area.area_code,
                    "display_name": area.display_name,
                    "is_vessel_only": area.is_vessel_only,
                    "sequence_no": area.sequence_no,
                    "status": instance.score_rows.get(area.area_code).status if area.area_code in instance.score_rows else None,
                    "remarks": instance.score_rows.get(area.area_code).remarks if area.area_code in instance.score_rows else "",
                }
                for area in instance.areas
            ],
            "findings": instance.findings,
        }
