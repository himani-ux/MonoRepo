from __future__ import annotations

from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError

from apps.safety.models import SafetyFieldHistory, SOIFinding, SOIInspection, SOIInspectionArea, SOITrainee, SOIVesselAreaMap
from apps.safety.repositories.soi_repo import SOIRepository
from apps.safety.services.crew_rotation_coverage import CrewRotationCoverageService
from apps.safety.services.field_history_recorder import (
    capture_model_state,
    parse_history_value,
    record_field_changes,
    resolve_actor_id,
    resolve_actor_role,
)
from apps.safety.services.signature_chain import SignatureChainService


SOI_CLOSE_SIGNATURE_FIELD = "soi_close_signature"
MASTER_ROLES = {"MASTER"}


class SOICloseService:
    def __init__(
        self,
        *,
        soi_repository: SOIRepository | None = None,
        crew_rotation_service: CrewRotationCoverageService | None = None,
        signature_service: SignatureChainService | None = None,
        inspection_model=SOIInspection,
        inspection_area_model=SOIInspectionArea,
        area_map_model=SOIVesselAreaMap,
        trainee_model=SOITrainee,
        finding_model=SOIFinding,
        field_history_model=SafetyFieldHistory,
        now_func=timezone.now,
    ) -> None:
        self.soi_repository = soi_repository or SOIRepository()
        self.crew_rotation_service = crew_rotation_service or CrewRotationCoverageService(now_func=now_func)
        self.signature_service = signature_service or SignatureChainService()
        self.inspection_model = inspection_model
        self.inspection_area_model = inspection_area_model
        self.area_map_model = area_map_model
        self.trainee_model = trainee_model
        self.finding_model = finding_model
        self.field_history_model = field_history_model
        self.now_func = now_func

    def get_close_snapshot(self, *, inspection: SOIInspection) -> dict[str, object]:
        refreshed = self.inspection_model.objects.get(pk=inspection.pk, is_deleted=False)
        return self._build_snapshot(refreshed)

    def close_inspection(
        self,
        *,
        inspection: SOIInspection,
        user,
        typed_name: str,
        device_fingerprint: str,
    ) -> dict[str, object]:
        self._assert_master_actor(user)
        signature = self.signature_service.validate_payload(
            typed_name=typed_name,
            device_fingerprint=device_fingerprint,
        )
        signed_at = self._coerce_datetime(self.now_func())
        actor_id = resolve_actor_id(user)

        with transaction.atomic():
            locked_inspection = self.inspection_model.objects.select_for_update().get(
                pk=inspection.pk,
                is_deleted=False,
            )
            if locked_inspection.state == SOIInspection.State.CLOSED:
                raise ValidationError("SOI inspection is already closed.")
            if locked_inspection.state != SOIInspection.State.REPORTED:
                raise ValidationError("Only reported SOI inspections can be closed.")

            selected_rows = list(
                self.inspection_area_model.objects.select_for_update().filter(
                    inspection_id=locked_inspection.id,
                ).order_by("area_id")
            )
            selected_area_ids = [int(row.area_id) for row in selected_rows]
            if not selected_area_ids:
                raise ValidationError("SOI inspection cannot close without at least one selected area.")
            unhandled_area_ids = [int(row.area_id) for row in selected_rows if not bool(row.inspected)]
            if unhandled_area_ids:
                raise ValidationError(
                    "SOI inspection cannot close until all selected areas are submitted as inspected: "
                    + ", ".join(str(area_id) for area_id in unhandled_area_ids)
                )
            unresolved_count = self.finding_model.objects.filter(
                inspection_id=locked_inspection.id,
                is_deleted=False,
                status__in=[SOIFinding.Status.OPEN, SOIFinding.Status.PENDING_CLOSURE],
            ).count()
            if unresolved_count:
                raise ValidationError("SOI inspection cannot close while findings are OPEN or PENDING_CLOSURE.")

            old_state = capture_model_state(
                locked_inspection,
                field_names=("state", "master_crew_id", "closed_at", "updated_by", "updated_date"),
            )
            locked_inspection.state = SOIInspection.State.CLOSED
            locked_inspection.master_crew_id = actor_id
            locked_inspection.closed_at = signed_at
            locked_inspection.updated_by = actor_id
            locked_inspection.updated_date = signed_at
            locked_inspection.save(
                update_fields=("state", "master_crew_id", "closed_at", "updated_by", "updated_date")
            )
            record_field_changes(
                locked_inspection,
                old_state,
                user=user,
                field_names=("state", "master_crew_id", "closed_at", "updated_by", "updated_date"),
                change_reason="Master closed SOI inspection.",
            )
            self.field_history_model.objects.create(
                parent_table=locked_inspection._meta.db_table,
                parent_id=locked_inspection.pk,
                field_name=SOI_CLOSE_SIGNATURE_FIELD,
                old_value=None,
                new_value={
                    "typed_name": signature.typed_name,
                    "signed_at": signed_at.isoformat(),
                    "device_fingerprint": signature.device_fingerprint,
                    "signed_by": actor_id,
                    "signed_role": resolve_actor_role(user),
                },
                change_reason="SOI inspection closed.",
                actor_user_id=actor_id,
                actor_role_code=resolve_actor_role(user),
                schema_version=locked_inspection.schema_version or 1,
            )

        refreshed = self.inspection_model.objects.get(pk=inspection.pk, is_deleted=False)
        snapshot = self._build_snapshot(refreshed)
        snapshot["signature"] = self._signature_snapshot_from_history(refreshed)
        return snapshot

    def _build_snapshot(self, inspection: SOIInspection) -> dict[str, object]:
        finding_rows = list(
            self.finding_model.objects.filter(
                inspection_id=inspection.id,
                is_deleted=False,
            ).only("status")
        )
        return {
            "inspection_id": inspection.id,
            "vessel_id": str(inspection.vessel_id),
            "inspection_reference": inspection.inspection_reference,
            "checklist_unique_id": inspection.checklist_unique_id,
            "planned_date": inspection.planned_date,
            "state": inspection.state,
            "closed_at": inspection.closed_at,
            "selected_areas": self.soi_repository.list_selected_areas(inspection.id),
            "trainees": self.soi_repository.list_trainees(inspection.id),
            "finding_summary": {
                "total_count": len(finding_rows),
                "open_count": sum(1 for row in finding_rows if row.status == SOIFinding.Status.OPEN),
                "master_approved_count": sum(
                    1 for row in finding_rows if row.status == SOIFinding.Status.MASTER_APPROVED
                ),
                "pending_closure_count": sum(
                    1 for row in finding_rows if row.status == SOIFinding.Status.PENDING_CLOSURE
                ),
                "closed_count": sum(1 for row in finding_rows if row.status == SOIFinding.Status.CLOSED),
                "carried_forward_count": sum(
                    1 for row in finding_rows if row.status == SOIFinding.Status.CARRIED_FORWARD
                ),
            },
            "crew_rotation": self.crew_rotation_service.get_summary(str(inspection.vessel_id)),
            "signature": self._signature_snapshot_from_history(inspection),
        }

    def _signature_snapshot_from_history(self, inspection: SOIInspection) -> dict[str, object] | None:
        row = (
            self.field_history_model.objects.filter(
                parent_table=inspection._meta.db_table,
                parent_id=inspection.pk,
                field_name=SOI_CLOSE_SIGNATURE_FIELD,
            )
            .order_by("-changed_at", "-id")
            .first()
        )
        if row is None or not row.new_value:
            return None
        payload = parse_history_value(row.new_value)
        if not isinstance(payload, dict):
            return None

        typed_name = str(payload.get("typed_name") or "").strip()
        signed_at = str(payload.get("signed_at") or "").strip()
        device_fingerprint = str(payload.get("device_fingerprint") or "").strip()
        if not typed_name or not signed_at or not device_fingerprint:
            return None
        return {
            "signer_display_name": typed_name,
            "signed_at": signed_at,
            "device_fingerprint_last8": device_fingerprint[-8:],
        }

    def _assert_master_actor(self, user) -> None:
        actor_role = resolve_actor_role(user)
        if actor_role not in MASTER_ROLES:
            raise PermissionDenied("SOI close is restricted to Master (D-GAP-M15).")

    def _coerce_datetime(self, value):
        if timezone.is_naive(value):
            return timezone.make_aware(value, timezone.get_current_timezone())
        return value
