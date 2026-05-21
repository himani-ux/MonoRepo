from __future__ import annotations

from django.utils import timezone
from rest_framework import serializers

from apps.safety.models import ChainOfCustody, EvidenceDeadlineTask, EvidenceItem, Incident, IncidentEvidence, WitnessInterview


TAB_KEY_TO_CODE = {
    "position": IncidentEvidence.TabCode.POSITION,
    "people": IncidentEvidence.TabCode.PEOPLE,
    "parts": IncidentEvidence.TabCode.PARTS,
    "paper": IncidentEvidence.TabCode.PAPER,
    "electronic": IncidentEvidence.TabCode.ELECTRONIC,
}


class IncidentEvidenceTabSerializer(serializers.ModelSerializer):
    class Meta:
        model = IncidentEvidence
        fields = ("public_id", "tab_code", "summary", "entry_count", "structured_data", "status_chip", "na_justification")


class IncidentPhase3TabWriteSerializer(serializers.Serializer):
    summary = serializers.CharField(required=False, allow_blank=True)
    entry_count = serializers.IntegerField(required=False, min_value=0)
    structured_data = serializers.JSONField(required=False)
    status_chip = serializers.CharField(required=False, allow_blank=True)
    na_justification = serializers.CharField(required=False, allow_blank=True, allow_null=True)


class IncidentPhase3WorkspaceWriteSerializer(serializers.Serializer):
    position = IncidentPhase3TabWriteSerializer(required=False)
    people = IncidentPhase3TabWriteSerializer(required=False)
    parts = IncidentPhase3TabWriteSerializer(required=False)
    paper = IncidentPhase3TabWriteSerializer(required=False)
    electronic = IncidentPhase3TabWriteSerializer(required=False)


class EvidenceItemMatrixSerializer(serializers.ModelSerializer):
    class Meta:
        model = EvidenceItem
        fields = ("id", "public_id", "finding", "pro_evidence", "con_evidence", "source_label", "comments", "created_date")
        read_only_fields = ("id", "public_id", "created_date")

    def create(self, validated_data):
        incident: Incident = self.context["incident"]
        user_id: str = self.context["user_id"]
        return EvidenceItem.objects.create(
            incident=incident,
            item_type=EvidenceItem.ItemType.MATRIX,
            title=validated_data.get("finding") or "Matrix row",
            created_by=user_id,
            updated_by=user_id,
            schema_version=incident.schema_version or 1,
            **validated_data,
        )


class EvidenceDeadlineTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = EvidenceDeadlineTask
        fields = ("id", "public_id", "task_code", "title", "due_at", "due_within", "severity", "status", "completed_at", "justification")


class EvidenceDeadlineTaskUpdateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=EvidenceDeadlineTask.Status.choices)
    justification = serializers.CharField(required=False, allow_blank=True, allow_null=True)


class ChainOfCustodySerializer(serializers.ModelSerializer):
    class Meta:
        model = ChainOfCustody
        fields = (
            "id",
            "public_id",
            "description",
            "collection_timestamp",
            "collector_name",
            "collector_signature",
            "storage_location",
            "witness_signature",
            "current_holder",
            "handover_log",
        )
        read_only_fields = ("id", "public_id", "handover_log")


class ChainOfCustodyCreateSerializer(serializers.Serializer):
    description = serializers.CharField()
    collection_timestamp = serializers.DateTimeField()
    collector_name = serializers.CharField()
    collector_signature = serializers.CharField()
    storage_location = serializers.CharField()
    witness_signature = serializers.CharField()
    current_holder = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs):
        if not attrs.get("witness_signature"):
            raise serializers.ValidationError(
                {"witness_signature": "Physical evidence requires witness signature per chain-of-custody protocol."}
            )
        return attrs

    def create(self, validated_data):
        incident: Incident = self.context["incident"]
        user_id: str = self.context["user_id"]
        current_holder = validated_data.pop("current_holder", "") or validated_data["collector_name"]
        evidence_item = EvidenceItem.objects.create(
            incident=incident,
            item_type=EvidenceItem.ItemType.PHYSICAL,
            title=validated_data["description"][:256],
            description=validated_data["description"],
            created_by=user_id,
            updated_by=user_id,
            schema_version=incident.schema_version or 1,
        )
        return ChainOfCustody.objects.create(
            incident=incident,
            evidence_item=evidence_item,
            current_holder=current_holder,
            created_by=user_id,
            updated_by=user_id,
            schema_version=incident.schema_version or 1,
            **validated_data,
        )


class ChainOfCustodyTransferSerializer(serializers.Serializer):
    chain_of_custody_id = serializers.IntegerField()
    handover_timestamp = serializers.DateTimeField()
    handover_from = serializers.CharField()
    handover_to = serializers.CharField()


class WitnessInterviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = WitnessInterview
        fields = (
            "id",
            "public_id",
            "witness_name",
            "interview_type",
            "reason_formal_impossible",
            "make_acquaintance_notes",
            "introduction_notes",
            "meeting_notes",
            "conclusion_notes",
            "question_rows",
            "read_back_confirmed",
            "witness_signature",
            "copy_to_witness_recorded",
            "is_final",
            "phase_count",
        )
        read_only_fields = ("id", "public_id", "is_final", "phase_count")

    def validate(self, attrs):
        interview_type = attrs.get("interview_type")
        notes = [
            attrs.get("make_acquaintance_notes"),
            attrs.get("introduction_notes"),
            attrs.get("meeting_notes"),
            attrs.get("conclusion_notes"),
        ]
        phase_count = sum(1 for note in notes if note and str(note).strip())
        attrs["phase_count"] = phase_count

        if interview_type == WitnessInterview.InterviewType.FORMAL:
            if (
                phase_count != 4
                or not attrs.get("read_back_confirmed")
                or not attrs.get("witness_signature")
                or not attrs.get("copy_to_witness_recorded")
            ):
                raise serializers.ValidationError(
                    {
                        "non_field_errors": [
                            "Formal interview requires all 4 phases plus read-back, witness signature, and copy-to-witness record."
                        ]
                    }
                )
            attrs["is_final"] = True
        elif interview_type == WitnessInterview.InterviewType.INFORMAL:
            if not attrs.get("reason_formal_impossible"):
                raise serializers.ValidationError(
                    {
                        "reason_formal_impossible": "Informal interview requires a reason explaining why formal interview was not possible."
                    }
                )
            attrs["is_final"] = False
        return attrs

    def create(self, validated_data):
        incident: Incident = self.context["incident"]
        user_id: str = self.context["user_id"]
        return WitnessInterview.objects.create(
            incident=incident,
            created_by=user_id,
            updated_by=user_id,
            schema_version=incident.schema_version or 1,
            **validated_data,
        )


def build_phase3_workspace_payload(incident: Incident) -> dict[str, object]:
    tab_rows = {row.tab_code: row for row in incident.evidence_tabs.all()}
    payload: dict[str, object] = {}
    for key, code in TAB_KEY_TO_CODE.items():
        row = tab_rows.get(code)
        if row is None:
            payload[key] = {
                "tab_code": code,
                "summary": "",
                "entry_count": 0,
                "structured_data": {},
                "status_chip": "",
                "na_justification": None,
            }
        else:
            payload[key] = IncidentEvidenceTabSerializer(row).data

    payload["chain_of_custody"] = ChainOfCustodySerializer(
        incident.chain_of_custody_rows.order_by("collection_timestamp", "id"),
        many=True,
    ).data
    payload["evidence_matrix"] = EvidenceItemMatrixSerializer(
        incident.evidence_items.filter(item_type=EvidenceItem.ItemType.MATRIX).order_by("id"),
        many=True,
    ).data
    payload["deadline_tasks"] = EvidenceDeadlineTaskSerializer(
        incident.evidence_deadline_tasks.order_by("due_at", "id"),
        many=True,
    ).data
    payload["interviews"] = WitnessInterviewSerializer(
        incident.witness_interviews.order_by("id"),
        many=True,
    ).data
    payload["refreshed_at"] = timezone.now()
    return payload
