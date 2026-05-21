from __future__ import annotations

from pathlib import PurePosixPath

from django.utils import timezone
from rest_framework import serializers

from apps.safety.models import EvidenceItem, Incident, IncidentEvidence

from .incident_phase4 import IncidentFactSerializer
from .near_miss import NearMissSerializer


NEAR_MISS_EVIDENCE_TYPE_TO_TAB = {
    "PHOTO": IncidentEvidence.TabCode.ELECTRONIC,
    "WITNESS_NOTE": IncidentEvidence.TabCode.PEOPLE,
    "CHECKLIST_ENTRY": IncidentEvidence.TabCode.PAPER,
    "DOCUMENT": IncidentEvidence.TabCode.PAPER,
    "OTHER": IncidentEvidence.TabCode.PAPER,
}


class NearMissAnalysisFactSerializer(IncidentFactSerializer):
    """Near-miss lightweight analysis reuses the shared fact-base contract only."""

    evidence_preview = serializers.SerializerMethodField()

    class Meta(IncidentFactSerializer.Meta):
        fields = IncidentFactSerializer.Meta.fields + ("evidence_preview",)
        read_only_fields = IncidentFactSerializer.Meta.read_only_fields + ("evidence_preview",)

    def get_evidence_preview(self, instance):
        evidence = instance.incident.evidence_items.filter(pk=instance.source_evidence_id).first()
        if evidence is None:
            return None
        metadata = evidence.metadata_json or {}
        attachment_path = str(metadata.get("attachment_path") or "").strip()
        content_type = str(metadata.get("content_type") or "").strip()
        if not attachment_path or not content_type.startswith("image/"):
            return None
        return {
            "attachment_path": attachment_path,
            "content_type": content_type,
            "file_name": metadata.get("file_name") or PurePosixPath(attachment_path).name,
            "preview_url": (
                f"/api/safety/near-miss/{instance.incident.public_id}/"
                f"analysis/evidence/{evidence.public_id}/photo/"
            ),
            "title": evidence.title,
        }


class NearMissEvidenceSourceCreateSerializer(serializers.Serializer):
    evidence_type = serializers.ChoiceField(choices=tuple((key, key) for key in NEAR_MISS_EVIDENCE_TYPE_TO_TAB))
    title = serializers.CharField(max_length=256)
    description = serializers.CharField()
    source_label = serializers.CharField(required=False, allow_blank=True)

    def create(self, validated_data):
        near_miss: Incident = self.context["incident"]
        actor_id: str = self.context["user_id"]
        evidence_type = validated_data["evidence_type"]
        tab_code = NEAR_MISS_EVIDENCE_TYPE_TO_TAB[evidence_type]
        tab_row, _ = IncidentEvidence.objects.get_or_create(
            incident=near_miss,
            tab_code=tab_code,
            defaults={
                "summary": f"Near miss {evidence_type.lower().replace('_', ' ')} evidence.",
                "entry_count": 0,
                "structured_data": {"source": "near_miss_analysis"},
                "status_chip": "Near miss evidence",
                "schema_version": near_miss.schema_version or 1,
                "created_by": actor_id,
                "updated_by": actor_id,
            },
        )
        metadata = {
            "near_miss_evidence_type": evidence_type,
            "recorded_at": timezone.now().isoformat(),
        }
        photo_metadata = self.context.get("photo_metadata")
        if isinstance(photo_metadata, dict):
            metadata.update(photo_metadata)
        evidence_item = EvidenceItem.objects.create(
            incident=near_miss,
            evidence_tab=tab_row,
            item_type=EvidenceItem.ItemType.PHYSICAL,
            title=validated_data["title"],
            description=validated_data["description"],
            source_label=validated_data.get("source_label", ""),
            metadata_json=metadata,
            created_by=actor_id,
            updated_by=actor_id,
            schema_version=near_miss.schema_version or 1,
        )
        tab_row.entry_count = max(int(tab_row.entry_count or 0) + 1, tab_row.items.count())
        tab_row.summary = validated_data["title"]
        tab_row.status_chip = f"{tab_row.entry_count} near-miss evidence source{'s' if tab_row.entry_count != 1 else ''}"
        tab_row.updated_by = actor_id
        tab_row.updated_date = timezone.now()
        tab_row.save(update_fields=("summary", "entry_count", "status_chip", "updated_by", "updated_date"))
        return evidence_item


def _ensure_default_near_miss_evidence_source(near_miss: Incident, *, actor_id: str) -> EvidenceItem:
    tab_row, created = IncidentEvidence.objects.get_or_create(
        incident=near_miss,
        tab_code=IncidentEvidence.TabCode.PAPER,
        defaults={
            "summary": "Near miss report narrative and reporter-submitted description.",
            "entry_count": 1,
            "structured_data": {
                "source": "near_miss_report",
                "incident_number": near_miss.incident_number,
            },
            "status_chip": "Report source",
            "schema_version": near_miss.schema_version or 1,
            "created_by": actor_id,
            "updated_by": actor_id,
        },
    )
    if not created and not (tab_row.summary or "").strip():
        tab_row.summary = "Near miss report narrative and reporter-submitted description."
        tab_row.entry_count = max(tab_row.entry_count or 0, 1)
        tab_row.updated_by = actor_id
        tab_row.save(update_fields=("summary", "entry_count", "updated_by"))

    default_item = near_miss.evidence_items.filter(
        item_type=EvidenceItem.ItemType.PHYSICAL,
        metadata_json__source="near_miss_report",
    ).first()
    if default_item is not None:
        return default_item

    return EvidenceItem.objects.create(
        incident=near_miss,
        evidence_tab=tab_row,
        item_type=EvidenceItem.ItemType.PHYSICAL,
        title="Near miss report narrative",
        description=near_miss.narrative or "Reporter-submitted near miss description.",
        source_label="NEAR_MISS_REPORT",
        metadata_json={
            "incident_number": near_miss.incident_number,
            "source": "near_miss_report",
        },
        created_by=actor_id,
        updated_by=actor_id,
        schema_version=near_miss.schema_version or 1,
    )


def _build_evidence_sources(near_miss: Incident, *, actor_id: str) -> list[dict[str, object]]:
    _ensure_default_near_miss_evidence_source(near_miss, actor_id=actor_id)
    sources: list[dict[str, object]] = []

    for row in near_miss.evidence_items.order_by("id"):
        sources.append(
            {
                "id": row.pk,
                "public_id": str(row.public_id),
                "label": row.title or f"Evidence item #{row.pk}",
                "preview": _build_evidence_item_preview(row, near_miss_public_id=str(near_miss.public_id)),
                "source_type": "EVIDENCE_ITEM",
            }
        )
    for row in near_miss.witness_interviews.order_by("id"):
        sources.append(
            {
                "id": row.pk,
                "public_id": str(row.public_id),
                "label": f"Witness note - {row.witness_name}",
                "source_type": "WITNESS_INTERVIEW",
            }
        )
    for row in near_miss.chain_of_custody_rows.order_by("id"):
        sources.append(
            {
                "id": row.pk,
                "public_id": str(row.public_id),
                "label": f"Physical evidence - {row.description[:80]}",
                "source_type": "CHAIN_OF_CUSTODY",
            }
        )
    return sources


def _build_evidence_item_preview(row: EvidenceItem, *, near_miss_public_id: str) -> dict[str, object] | None:
    metadata = row.metadata_json or {}
    attachment_path = str(metadata.get("attachment_path") or "").strip()
    content_type = str(metadata.get("content_type") or "").strip()
    if not attachment_path or not content_type.startswith("image/"):
        return None
    return {
        "attachment_path": attachment_path,
        "content_type": content_type,
        "file_name": metadata.get("file_name") or PurePosixPath(attachment_path).name,
        "preview_url": f"/api/safety/near-miss/{near_miss_public_id}/analysis/evidence/{row.public_id}/photo/",
        "title": row.title,
    }


def build_near_miss_analysis_payload(
    near_miss: Incident,
    *,
    serializer_context: dict[str, object] | None = None,
    fact_context: dict[str, object] | None = None,
) -> dict[str, object]:
    actor_id = str((fact_context or {}).get("user_id") or "system")
    return {
        "analysis_mode": "FACT_TREE_ONLY",
        "near_miss": NearMissSerializer(near_miss, context=serializer_context or {}).data,
        "facts": NearMissAnalysisFactSerializer(
            near_miss.facts.order_by("sequence_index", "id"),
            many=True,
            context=fact_context or {"incident": near_miss, "user_id": "system"},
        ).data,
        "evidence_sources": _build_evidence_sources(near_miss, actor_id=actor_id),
        "requirements": {
            "causal_layering_required": False,
            "physical_verification_required": False,
            "system_action_required": False,
        },
    }
