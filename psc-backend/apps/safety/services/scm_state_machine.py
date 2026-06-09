from __future__ import annotations
from dataclasses import dataclass
import hashlib

from django.utils import timezone
from rest_framework import serializers

from apps.safety.models import SCMMeeting, SCMSignature, SafetyFieldHistory
from apps.safety.services.field_history_recorder import (
    capture_model_state,
    record_field_changes,
    resolve_actor_id,
    resolve_actor_role,
)


SCM_SIGNOFF_SIGNATURE_FIELD = "scm_signoff_signature"


@dataclass(frozen=True)
class SCMSignaturePayload:
    typed_name: str
    device_fingerprint: str
    signed_at: object


class SCMStateMachine:
    READ_ONLY_MESSAGE = "Closed SCM meetings are read-only in the handover workspace."
    OFFICE_REVIEW_LOCK_MESSAGE = "SCM meetings cannot be edited after office review is recorded."
    SIGNOFF_STATE_MESSAGE = "Only submitted or reopened SCM meetings can be signed off in the handover workspace."
    DEVICE_FINGERPRINT_MAX_LENGTH = 128

    def _compact_device_fingerprint(self, value: str) -> str:
        normalized = (value or "").strip()
        if len(normalized) <= self.DEVICE_FINGERPRINT_MAX_LENGTH:
            return normalized
        digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
        return f"sha256:{digest}"

    def validate_signature_payload(self, *, typed_name: str, device_fingerprint: str) -> SCMSignaturePayload:
        errors: dict[str, str] = {}
        normalized_name = (typed_name or "").strip()
        normalized_fingerprint = self._compact_device_fingerprint(device_fingerprint)

        if len(normalized_name) < 3:
            errors["typed_name"] = "Digital signature requires the typed full name."
        if not normalized_fingerprint:
            errors["device_fingerprint"] = "Digital signature requires a device fingerprint."

        if errors:
            raise serializers.ValidationError(errors)

        return SCMSignaturePayload(
            typed_name=normalized_name,
            device_fingerprint=normalized_fingerprint,
            signed_at=timezone.now(),
        )

    def ensure_mutable(self, meeting: SCMMeeting) -> None:
        if meeting.office_comment_at is not None or meeting.state == SCMMeeting.State.CLOSED:
            raise serializers.ValidationError({"state": [self.READ_ONLY_MESSAGE]})

    def ensure_editable_until_office_review(self, meeting: SCMMeeting) -> None:
        if meeting.office_comment_at is not None:
            raise serializers.ValidationError({"state": [self.OFFICE_REVIEW_LOCK_MESSAGE]})

    def ensure_signoff_ready(self, meeting: SCMMeeting) -> None:
        if meeting.state not in {SCMMeeting.State.SUBMITTED, SCMMeeting.State.REOPENED}:
            raise serializers.ValidationError({"state": [self.SIGNOFF_STATE_MESSAGE]})

    def submit_for_signoff(self, meeting: SCMMeeting, *, user) -> SCMMeeting:
        if meeting.state != SCMMeeting.State.DRAFT:
            raise serializers.ValidationError({"state": ["Only draft SCM meetings can be finalised for sign-off."]})

        actor_id = resolve_actor_id(user)
        submitted_at = timezone.now()
        old_state = capture_model_state(
            meeting,
            field_names=("state", "updated_by", "updated_date"),
        )
        meeting.state = SCMMeeting.State.SUBMITTED
        meeting.updated_by = actor_id
        meeting.updated_date = submitted_at
        meeting.save(update_fields=("state", "updated_by", "updated_date"))
        record_field_changes(
            meeting,
            old_state,
            user=user,
            field_names=("state", "updated_by", "updated_date"),
            change_reason="SCM finalised for Master sign-off.",
        )
        return meeting

    def sign_off(
        self,
        meeting: SCMMeeting,
        *,
        typed_name: str,
        device_fingerprint: str,
        user,
    ) -> SCMSignaturePayload:
        self.ensure_signoff_ready(meeting)
        payload = self.validate_signature_payload(
            typed_name=typed_name,
            device_fingerprint=device_fingerprint,
        )

        actor_id = resolve_actor_id(user)
        actor_role = resolve_actor_role(user)
        old_state = capture_model_state(
            meeting,
            field_names=(
                "state",
                "master_signed_off_at",
                "master_signed_off_by",
                "updated_by",
                "updated_date",
            ),
        )

        meeting.state = SCMMeeting.State.SIGNED_OFF
        meeting.master_signed_off_at = payload.signed_at
        meeting.master_signed_off_by = actor_id
        meeting.updated_by = actor_id
        meeting.updated_date = payload.signed_at
        meeting.save(
            update_fields=[
                "state",
                "master_signed_off_at",
                "master_signed_off_by",
                "updated_by",
                "updated_date",
            ]
        )
        record_field_changes(
            meeting,
            old_state,
            user=user,
            field_names=(
                "state",
                "master_signed_off_at",
                "master_signed_off_by",
                "updated_by",
                "updated_date",
            ),
            change_reason="SCM sign-off completed.",
        )
        SafetyFieldHistory.objects.create(
            parent_table=meeting._meta.db_table,
            parent_id=meeting.pk,
            field_name=SCM_SIGNOFF_SIGNATURE_FIELD,
            old_value=None,
            new_value={
                "typed_name": payload.typed_name,
                "device_fingerprint": payload.device_fingerprint,
                "signed_at": payload.signed_at.isoformat(),
                "signed_by": actor_id,
                "signed_role": actor_role,
            },
            change_reason="SCM sign-off completed.",
            actor_user_id=actor_id,
            actor_role_code=actor_role,
            schema_version=meeting.schema_version or 1,
        )
        self.record_signature(
            meeting,
            signer_role=SCMSignature.SignerRole.MASTER,
            signer_crew_id=actor_id,
            display_name=payload.typed_name,
            typed_name=payload.typed_name,
            device_fingerprint=payload.device_fingerprint,
            signed_at=payload.signed_at,
            user=user,
        )
        return payload

    def record_signature(
        self,
        meeting: SCMMeeting,
        *,
        signer_role: str,
        signer_crew_id: str,
        display_name: str,
        typed_name: str,
        device_fingerprint: str,
        signed_at,
        user,
    ) -> SCMSignature:
        payload = self.validate_signature_payload(
            typed_name=typed_name,
            device_fingerprint=device_fingerprint,
        )
        return SCMSignature.objects.update_or_create(
            meeting_id=meeting.id,
            signer_role=signer_role,
            signer_crew_id=str(signer_crew_id),
            defaults={
                "display_name": display_name or payload.typed_name,
                "typed_name": payload.typed_name,
                "device_fingerprint": payload.device_fingerprint,
                "signed_at": signed_at or payload.signed_at,
                "created_by": resolve_actor_id(user),
                "schema_version": meeting.schema_version or 1,
            },
        )[0]
