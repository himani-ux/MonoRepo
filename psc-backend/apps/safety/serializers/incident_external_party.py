from __future__ import annotations

from rest_framework import serializers

from apps.safety.models import ExternalPartyInjury


BLANK_TO_NULL_FIELDS = {
    "cost_deviation",
    "cost_doctor_visits",
    "cost_evacuation",
    "cost_man_hours_lost",
    "cost_medicines_onboard",
    "cost_miscellaneous",
    "cost_off_hire",
    "cost_repatriation",
    "cost_vessel_delays",
    "crew_age",
    "departure_date",
    "shore_assistance_required",
    "total_estimated_cost",
}


class ExternalPartyInjurySerializer(serializers.ModelSerializer):
    incident_id = serializers.IntegerField(read_only=True)

    class Meta:
        model = ExternalPartyInjury
        fields = (
            "id",
            "incident_id",
            "injured_person_type",
            "party_name",
            "party_type",
            "company_name",
            "severity",
            "crew_rank",
            "crew_age",
            "crew_activity_type",
            "shore_assistance_required",
            "vessel_location",
            "onboard_location",
            "last_port",
            "departure_date",
            "vessel_condition",
            "what_happened_narrative",
            "nature_of_injury",
            "source_of_injury",
            "affected_body_areas",
            "first_aid_details",
            "why_it_happened_analysis",
            "regulation_or_procedure_breach",
            "risk_assessment_carried_out",
            "toolbox_meeting_carried_out",
            "prevention_action_taken_required",
            "ocimf_fatality",
            "ocimf_permanent_total_disability",
            "ocimf_permanent_partial_disability",
            "ocimf_lost_workday_case",
            "ocimf_restricted_workday_case",
            "ocimf_medical_treatment_case",
            "ocimf_first_aid_case",
            "cost_medicines_onboard",
            "cost_doctor_visits",
            "cost_repatriation",
            "cost_evacuation",
            "cost_off_hire",
            "cost_vessel_delays",
            "cost_man_hours_lost",
            "cost_deviation",
            "cost_miscellaneous",
            "miscellaneous_expenses_reason",
            "total_estimated_cost",
            "notes",
            "schema_version",
            "created_by",
            "created_date",
            "updated_by",
            "updated_date",
        )
        read_only_fields = (
            "id",
            "incident_id",
            "created_by",
            "created_date",
            "updated_by",
            "updated_date",
        )
        extra_kwargs = {
            "company_name": {"required": False, "allow_blank": True},
            "injured_person_type": {"required": False},
            "notes": {"required": False, "allow_blank": True, "allow_null": True},
            "party_name": {"required": False, "allow_blank": True},
            "party_type": {"required": False, "allow_blank": True},
            "severity": {"required": False, "allow_blank": True},
        }

    def to_internal_value(self, data):
        mutable_data = dict(data)
        for field_name in BLANK_TO_NULL_FIELDS:
            if mutable_data.get(field_name) == "":
                mutable_data[field_name] = None
        return super().to_internal_value(mutable_data)

    def validate(self, attrs):
        attrs = super().validate(attrs)
        injured_person_type = attrs.get(
            "injured_person_type",
            getattr(self.instance, "injured_person_type", ExternalPartyInjury.InjuredPersonType.NON_CREW),
        )
        if injured_person_type == ExternalPartyInjury.InjuredPersonType.NON_CREW:
            missing_fields = {
                field_name: "This field is required for non-crew injury."
                for field_name in ("party_name", "party_type", "company_name", "severity")
                if not str(attrs.get(field_name, getattr(self.instance, field_name, "")) or "").strip()
            }
            if missing_fields:
                raise serializers.ValidationError(missing_fields)

        if attrs.get("vessel_condition") not in (None, "", "LOADED", "BALLAST"):
            raise serializers.ValidationError({"vessel_condition": "Select loaded or ballast."})
        for tri_state_field in ("risk_assessment_carried_out", "toolbox_meeting_carried_out"):
            if attrs.get(tri_state_field) not in (None, "", "YES", "NO", "NA"):
                raise serializers.ValidationError({tri_state_field: "Select yes, no, or NA."})

        for forbidden_key in attrs:
            key = forbidden_key.lower()
            if "acting" in key or "deputy" in key:
                raise serializers.ValidationError(
                    {
                        forbidden_key: (
                            "Acting-role / deputy-chain concepts not supported "
                            "(D-GAP-A3 / A4)."
                        )
                    }
                )
        return attrs
