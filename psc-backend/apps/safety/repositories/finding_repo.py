from __future__ import annotations

from collections.abc import Mapping
from datetime import timedelta
import uuid

from django.db import transaction
from django.utils import timezone

from apps.safety.models import SOIFinding, SOIInspection, SOIInspectionArea, SOIVesselAreaMap
from apps.safety.services.soi_schema_guard import ensure_soi_runtime_schema

from .base import BaseRepository


class FindingRepository(BaseRepository):
    def __init__(
        self,
        *,
        finding_model=SOIFinding,
        inspection_model=SOIInspection,
        inspection_area_model=SOIInspectionArea,
        area_map_model=SOIVesselAreaMap,
        now_func=timezone.now,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.finding_model = finding_model
        self.inspection_model = inspection_model
        self.inspection_area_model = inspection_area_model
        self.area_map_model = area_map_model
        self.now_func = now_func

    def list_for_inspection(self, inspection_id):
        return self.finding_model.objects.filter(
            inspection_id=inspection_id,
            is_deleted=False,
        ).order_by("-created_date", "-id")

    def selected_area_ids(self, inspection_id) -> set[int]:
        return set(
            self.inspection_area_model.objects.filter(inspection_id=inspection_id).values_list("area_id", flat=True)
        )

    def create_finding(
        self,
        *,
        inspection: SOIInspection,
        payload: Mapping[str, object],
        actor_id: str,
    ) -> SOIFinding:
        ensure_soi_runtime_schema()
        data = dict(payload)
        if not data.get("assigned_crew_id"):
            data["assigned_crew_id"] = inspection.safety_officer_crew_id
        data.setdefault("status", SOIFinding.Status.OPEN)
        data.setdefault("id", uuid.uuid4().hex)
        data.setdefault("carried_forward_count", 0)
        data.setdefault("schema_version", 1)
        data.setdefault("is_deleted", False)
        data.setdefault("created_by", actor_id)
        if data.get("created_date") is None:
            data["created_date"] = self.now_func()
        data.setdefault("updated_by", actor_id)
        finding_id = self._insert_finding(inspection_id=inspection.id, data=data)
        return self.finding_model.objects.get(pk=finding_id)

    def _insert_finding(self, *, inspection_id, data: Mapping[str, object]):
        def uuid_storage_value(value):
            if isinstance(value, uuid.UUID):
                return value.hex
            if value is None:
                return None
            return str(value).replace("-", "")

        field_names = [
            "id",
            "inspection_id",
            "area_id",
            "item_id",
            "title",
            "description",
            "severity",
            "priority",
            "mscat_category_id",
            "mscat_subcode_id",
            "shell_tag",
            "assigned_crew_id",
            "due_date",
            "proposed_action",
            "status",
            "carried_forward_count",
            "photo_attachment_path",
            "master_approved_at",
            "master_approved_by",
            "closed_at",
            "closure_note",
            "schema_version",
            "is_deleted",
            "created_by",
            "created_date",
            "updated_by",
            "updated_date",
        ]
        insert_data = {
            "inspection_id": uuid_storage_value(inspection_id),
            **dict(data),
        }
        insert_data["id"] = uuid_storage_value(insert_data.get("id")) or uuid.uuid4().hex
        insert_data["item_id"] = uuid_storage_value(insert_data.get("item_id"))
        model_fields = {field.name: field for field in self.finding_model._meta.concrete_fields}
        quote_name = self.connection.ops.quote_name
        table_name = quote_name(self.finding_model._meta.db_table)
        columns = ", ".join(quote_name(model_fields[field_name].column) for field_name in field_names)
        placeholders = ", ".join(["%s"] * len(field_names))
        values = [insert_data.get(field_name) for field_name in field_names]

        with self.connection.cursor() as cursor:
            if self.connection.vendor == "microsoft":
                id_column = quote_name(self.finding_model._meta.pk.column)
                cursor.execute(
                    f"INSERT INTO {table_name} ({columns}) OUTPUT INSERTED.{id_column} VALUES ({placeholders})",
                    values,
                )
                row = cursor.fetchone()
                if row is None:
                    raise RuntimeError("SOI finding insert did not return a new id.")
                return row[0]

            cursor.execute(
                f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})",
                values,
            )
            return insert_data["id"]

    def submit_areas(
        self,
        *,
        inspection: SOIInspection,
        submitted_area_ids: list[int],
        actor_id: str,
    ) -> dict[str, object]:
        normalized_ids = sorted({int(area_id) for area_id in submitted_area_ids})
        now_value = self.now_func()
        due_at = now_value + timedelta(days=90)

        with transaction.atomic():
            locked_inspection = self.inspection_model.objects.select_for_update().get(
                pk=inspection.pk,
                is_deleted=False,
            )
            if locked_inspection.state == SOIInspection.State.CLOSED:
                raise ValueError("Closed SOI inspections are read-only.")

            selected_rows = list(
                self.inspection_area_model.objects.select_for_update().filter(
                    inspection_id=locked_inspection.id,
                )
            )
            selected_area_ids = {int(row.area_id) for row in selected_rows}
            invalid_area_ids = [area_id for area_id in normalized_ids if area_id not in selected_area_ids]
            if invalid_area_ids:
                raise ValueError(
                    "Submitted area ids are not part of the downloaded inspection: "
                    + ", ".join(str(area_id) for area_id in invalid_area_ids)
                )

            self.inspection_area_model.objects.filter(
                inspection_id=locked_inspection.id,
                area_id__in=normalized_ids,
            ).update(
                inspected=True,
                last_inspected_at=now_value,
            )

            existing_maps = {
                int(row.area_id): row
                for row in self.area_map_model.objects.select_for_update().filter(
                    vessel_id=str(locked_inspection.vessel_id),
                    area_id__in=normalized_ids,
                )
            }
            create_rows = []
            for area_id in normalized_ids:
                existing = existing_maps.get(area_id)
                if existing is None:
                    create_rows.append(
                        self.area_map_model(
                            vessel_id=str(locked_inspection.vessel_id),
                            area_id=area_id,
                            applicable=True,
                            last_inspected_at=now_value,
                            due_at=due_at,
                            schema_version=1,
                        )
                    )
                    continue
                existing.last_inspected_at = now_value
                existing.due_at = due_at
                existing.save(update_fields=["last_inspected_at", "due_at"])

            if create_rows:
                self.area_map_model.objects.bulk_create(create_rows)

            refreshed_rows = list(
                self.inspection_area_model.objects.filter(inspection_id=locked_inspection.id).order_by("area_id")
            )
            remaining_area_ids = [
                int(row.area_id)
                for row in refreshed_rows
                if not bool(row.inspected)
            ]

            update_fields: dict[str, object] = {
                "fieldwork_started_at": locked_inspection.fieldwork_started_at or now_value,
                "updated_by": actor_id,
                "updated_date": now_value,
            }
            if not remaining_area_ids:
                update_fields["state"] = SOIInspection.State.REPORTED
                update_fields["reported_at"] = locked_inspection.reported_at or now_value
            self.inspection_model.objects.filter(pk=locked_inspection.pk).update(**update_fields)

        refreshed = self.inspection_model.objects.get(pk=inspection.pk, is_deleted=False)
        return {
            "checklist_unique_id": refreshed.checklist_unique_id,
            "inspection_id": refreshed.id,
            "remaining_area_ids": remaining_area_ids,
            "reported_at": refreshed.reported_at.isoformat() if refreshed.reported_at else None,
            "state": refreshed.state,
            "submitted_area_ids": normalized_ids,
            "total_selected_area_count": len(refreshed_rows),
        }
