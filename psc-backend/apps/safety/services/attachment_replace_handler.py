from __future__ import annotations
import os
from dataclasses import dataclass
from pathlib import Path

from django.db import connection
from django.utils import timezone

from apps.safety.models import SafetyFieldHistory
from apps.safety.services.field_history_recorder import resolve_actor_id, resolve_actor_role


@dataclass(frozen=True)
class AttachmentReplaceResult:
    absolute_path: str
    relative_path: str
    replaced: bool
    audit_row_id: int | None


class AttachmentReplaceHandler:
    def __init__(
        self,
        *,
        field_history_model=SafetyFieldHistory,
        storage_root: str | os.PathLike[str] | None = None,
    ) -> None:
        default_root = Path.cwd() / "var" / "www" / "ksm_uploads" / "safety"
        self.field_history_model = field_history_model
        self.storage_root = Path(storage_root or os.getenv("SAFETY_EXPORT_ROOT") or default_root).resolve(strict=False)

    def replace_in_place(
        self,
        *,
        relative_path: str,
        content: bytes,
        user,
        parent_table: str,
        parent_id: int,
        field_name: str = "attachment_replace",
        change_reason: str | None = None,
    ) -> AttachmentReplaceResult:
        target_path = self._resolve_target(relative_path)
        target_path.parent.mkdir(parents=True, exist_ok=True)

        replaced = target_path.exists()
        old_value = self._serialize_metadata(target_path) if replaced else None
        target_path.write_bytes(content)
        new_value = self._serialize_metadata(target_path)

        audit_row_id = None
        if self.field_history_model._meta.db_table in self._table_names():
            row = self.field_history_model.objects.create(
                parent_table=parent_table,
                parent_id=parent_id,
                field_name=field_name,
                old_value=old_value,
                new_value=new_value,
                change_reason=change_reason
                or "Attachment stored with same-filename replace-in-place semantics (D-GAP-M02).",
                actor_user_id=resolve_actor_id(user),
                actor_role_code=resolve_actor_role(user),
                schema_version=1,
            )
            audit_row_id = int(row.pk)

        return AttachmentReplaceResult(
            absolute_path=str(target_path),
            relative_path=str(target_path.relative_to(self.storage_root)).replace("\\", "/"),
            replaced=replaced,
            audit_row_id=audit_row_id,
        )

    def _resolve_target(self, relative_path: str) -> Path:
        normalized = str(relative_path or "").strip().replace("\\", "/").lstrip("/")
        if not normalized:
            raise ValueError("relative_path is required.")

        target_path = (self.storage_root / normalized).resolve(strict=False)
        try:
            target_path.relative_to(self.storage_root)
        except ValueError as exc:
            raise ValueError("Attachment path must stay within the configured Safety storage root.") from exc
        return target_path

    def _serialize_metadata(self, path: Path) -> dict[str, object]:
        stat_result = path.stat()
        return {
            "absolute_path": str(path),
            "relative_path": str(path.relative_to(self.storage_root)).replace("\\", "/"),
            "file_name": path.name,
            "byte_size": int(stat_result.st_size),
            "recorded_at": timezone.now().isoformat(),
            "replace_in_place": True,
        }

    @staticmethod
    def _table_names() -> set[str]:
        return set(connection.introspection.table_names())
