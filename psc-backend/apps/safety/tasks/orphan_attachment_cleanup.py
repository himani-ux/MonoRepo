from __future__ import annotations
import os
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

from django.db import connection
from django.utils import timezone

from apps.safety.models import EvidenceItem, Incident, SafetyFieldHistory, SCMMeeting, SOIFinding, SOIInspection
from apps.safety.services.field_history_recorder import parse_history_value


@dataclass(frozen=True)
class AttachmentDeleteResult:
    deleted_paths: list[str]
    missing_paths: list[str]
    kept_paths: list[str]
    audit_row_ids: list[int]


class OrphanAttachmentCleanupService:
    _PATH_HINT_TOKENS = ("attachment", "path", "file", "scan", "photo", "evidence")
    _IGNORED_HISTORY_FIELDS = {
        "incident_pdf_export",
        "near_miss_pdf_export",
        "scm_pdf_export",
        "soi_summary_pdf_export",
        "incident_msc_mepc3_export",
        "dashboard_export",
        "auditor_bundle_export",
        "retention_hard_delete",
        "retention_attachment_purge",
        "orphan_attachment_cleanup",
    }
    _IGNORED_JSON_PATH_KEYS = {"download_path", "export_path", "file_name"}
    _PATH_SUFFIXES = {
        ".csv",
        ".doc",
        ".docx",
        ".gif",
        ".jpeg",
        ".jpg",
        ".pdf",
        ".png",
        ".txt",
        ".xls",
        ".xlsx",
    }
    _SKIPPED_ROOT_SEGMENTS = {"exports"}
    system_parent_table = "system_attachment_store"

    def __init__(
        self,
        *,
        incident_model=Incident,
        scm_model=SCMMeeting,
        soi_model=SOIInspection,
        soi_finding_model=SOIFinding,
        evidence_item_model=EvidenceItem,
        field_history_model=SafetyFieldHistory,
        storage_root: str | os.PathLike[str] | None = None,
    ) -> None:
        default_root = Path.cwd() / "var" / "www" / "ksm_uploads" / "safety"
        self.incident_model = incident_model
        self.scm_model = scm_model
        self.soi_model = soi_model
        self.soi_finding_model = soi_finding_model
        self.evidence_item_model = evidence_item_model
        self.field_history_model = field_history_model
        self.storage_root = Path(storage_root or os.getenv("SAFETY_EXPORT_ROOT") or default_root).resolve(strict=False)

    def cleanup_orphans(self, *, now=None) -> AttachmentDeleteResult:
        if not self.storage_root.exists():
            return AttachmentDeleteResult([], [], [], [])

        referenced_paths = self.collect_referenced_paths()
        deleted_paths: list[str] = []
        kept_paths: list[str] = []
        audit_row_ids: list[int] = []
        resolved_now = now or timezone.now()

        for file_path in self._iter_candidate_files():
            normalized = str(file_path.resolve(strict=False))
            if normalized in referenced_paths:
                kept_paths.append(normalized)
                continue

            audit_parent_id = int(resolved_now.timestamp() * 1000) + len(audit_row_ids) + 1
            result = self.delete_paths(
                [normalized],
                now=resolved_now,
                reason="Attachment file removed because no live Safety parent record still references it.",
                audit_parent_table=self.system_parent_table,
                audit_parent_id=audit_parent_id,
                field_name="orphan_attachment_cleanup",
            )
            deleted_paths.extend(result.deleted_paths)
            audit_row_ids.extend(result.audit_row_ids)

        return AttachmentDeleteResult(
            deleted_paths=deleted_paths,
            missing_paths=[],
            kept_paths=kept_paths,
            audit_row_ids=audit_row_ids,
        )

    def collect_referenced_paths(self) -> set[str]:
        table_names = self._table_names()
        referenced: set[str] = set()

        if self.evidence_item_model._meta.db_table in table_names:
            for row in self.evidence_item_model.objects.all().values_list("metadata_json", flat=True):
                referenced.update(self._normalize_paths(self._extract_paths_from_json(row)))

        if self.soi_finding_model._meta.db_table in table_names:
            values = self.soi_finding_model.objects.filter(is_deleted=False).values_list("photo_attachment_path", flat=True)
            referenced.update(self._normalize_paths(values))

        if self.field_history_model._meta.db_table in table_names:
            for row in self.field_history_model.objects.all().only("field_name", "old_value", "new_value"):
                field_name = str(getattr(row, "field_name", "")).strip().lower()
                if field_name in self._IGNORED_HISTORY_FIELDS:
                    continue
                referenced.update(self._extract_paths_from_history_payload(row.old_value))
                referenced.update(self._extract_paths_from_history_payload(row.new_value))

        return referenced

    def collect_paths_for_parent(self, *, parent_table: str, parent_id: int) -> list[str]:
        table_names = self._table_names()
        normalized_parent_table = str(parent_table or "").strip()
        collected: list[str] = []

        if normalized_parent_table == self.incident_model._meta.db_table:
            if self.evidence_item_model._meta.db_table in table_names:
                rows = self.evidence_item_model.objects.filter(incident_id=parent_id).values_list("metadata_json", flat=True)
                for row in rows:
                    collected.extend(self._extract_paths_from_json(row))
            collected.extend(self._extract_paths_from_field_history(parent_table=normalized_parent_table, parent_id=parent_id))

        elif normalized_parent_table == self.scm_model._meta.db_table:
            collected.extend(self._extract_paths_from_field_history(parent_table=normalized_parent_table, parent_id=parent_id))

        elif normalized_parent_table == self.soi_model._meta.db_table:
            if self.soi_finding_model._meta.db_table in table_names:
                findings = self.soi_finding_model.objects.filter(inspection_id=parent_id).only("id", "photo_attachment_path")
                for finding in findings:
                    if finding.photo_attachment_path:
                        collected.append(str(finding.photo_attachment_path))
                    collected.extend(
                        self._extract_paths_from_field_history(
                            parent_table=self.soi_finding_model._meta.db_table,
                            parent_id=int(finding.pk),
                        )
                    )
            collected.extend(self._extract_paths_from_field_history(parent_table=normalized_parent_table, parent_id=parent_id))

        return list(self._normalize_paths(collected))

    def delete_paths(
        self,
        raw_paths: Sequence[str],
        *,
        now=None,
        reason: str,
        audit_parent_table: str,
        audit_parent_id: int,
        field_name: str,
    ) -> AttachmentDeleteResult:
        resolved_now = now or timezone.now()
        deleted_paths: list[str] = []
        missing_paths: list[str] = []
        audit_row_ids: list[int] = []
        seen: set[str] = set()

        for raw_path in raw_paths:
            resolved = self._resolve_storage_path(raw_path)
            if resolved is None:
                continue

            normalized = str(resolved)
            if normalized in seen:
                continue
            seen.add(normalized)

            if not resolved.exists():
                missing_paths.append(normalized)
                continue

            old_value = self._build_file_metadata(resolved, observed_at=resolved_now)
            resolved.unlink()
            deleted_paths.append(normalized)

            history_id = self._record_system_audit(
                parent_table=audit_parent_table,
                parent_id=audit_parent_id,
                field_name=field_name,
                old_value=old_value,
                new_value=None,
                change_reason=reason,
            )
            if history_id is not None:
                audit_row_ids.append(history_id)

        return AttachmentDeleteResult(
            deleted_paths=deleted_paths,
            missing_paths=missing_paths,
            kept_paths=[],
            audit_row_ids=audit_row_ids,
        )

    def _extract_paths_from_field_history(self, *, parent_table: str, parent_id: int) -> list[str]:
        if self.field_history_model._meta.db_table not in self._table_names():
            return []

        rows = (
            self.field_history_model.objects.filter(parent_table=parent_table, parent_id=parent_id)
            .only("field_name", "old_value", "new_value")
            .order_by("id")
        )
        extracted: list[str] = []
        for row in rows:
            field_name = str(getattr(row, "field_name", "")).strip().lower()
            if field_name in self._IGNORED_HISTORY_FIELDS:
                continue
            extracted.extend(self._extract_paths_from_history_payload(row.old_value))
            extracted.extend(self._extract_paths_from_history_payload(row.new_value))
        return extracted

    def _extract_paths_from_history_payload(self, payload) -> list[str]:
        if payload in (None, ""):
            return []
        parsed = parse_history_value(payload)
        if parsed in (None, ""):
            return []
        return [str(path) for path in self._normalize_paths(self._extract_paths_from_json(parsed))]

    def _extract_paths_from_json(self, value, *, key_hint: str = "") -> list[str]:
        paths: list[str] = []
        if isinstance(value, Mapping):
            for key, nested_value in value.items():
                paths.extend(self._extract_paths_from_json(nested_value, key_hint=str(key)))
            return paths

        if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
            for nested_value in value:
                paths.extend(self._extract_paths_from_json(nested_value, key_hint=key_hint))
            return paths

        if isinstance(value, str):
            normalized = value.strip()
            if self._looks_like_attachment_path(normalized, key_hint=key_hint):
                return [normalized]
        return paths

    def _looks_like_attachment_path(self, value: str, *, key_hint: str) -> bool:
        if not value:
            return False
        lower_key = key_hint.strip().lower()
        if lower_key in self._IGNORED_JSON_PATH_KEYS:
            return False
        if lower_key and not any(token in lower_key for token in self._PATH_HINT_TOKENS):
            return False
        candidate = Path(value)
        if candidate.suffix.lower() not in self._PATH_SUFFIXES:
            return False
        return candidate.is_absolute() or len(candidate.parts) > 1

    def _normalize_paths(self, values: Sequence[str]) -> set[str]:
        normalized: set[str] = set()
        for raw_value in values:
            resolved = self._resolve_storage_path(raw_value)
            if resolved is not None:
                normalized.add(str(resolved))
        return normalized

    def _resolve_storage_path(self, value) -> Path | None:
        raw_value = str(value or "").strip()
        if not raw_value:
            return None

        candidate = Path(raw_value)
        if candidate.is_absolute():
            resolved = candidate.resolve(strict=False)
        else:
            resolved = (self.storage_root / candidate).resolve(strict=False)

        try:
            resolved.relative_to(self.storage_root)
        except ValueError:
            return None
        return resolved

    def _iter_candidate_files(self):
        for file_path in self.storage_root.rglob("*"):
            if not file_path.is_file():
                continue
            relative_parts = {part.lower() for part in file_path.relative_to(self.storage_root).parts}
            if relative_parts & self._SKIPPED_ROOT_SEGMENTS:
                continue
            yield file_path

    def _build_file_metadata(self, path: Path, *, observed_at) -> dict[str, object]:
        stat_result = path.stat()
        try:
            relative_path = str(path.relative_to(self.storage_root))
        except ValueError:
            relative_path = str(path)
        return {
            "absolute_path": str(path),
            "relative_path": relative_path.replace("\\", "/"),
            "file_name": path.name,
            "byte_size": int(stat_result.st_size),
            "observed_at": observed_at.isoformat(),
        }

    def _record_system_audit(
        self,
        *,
        parent_table: str,
        parent_id: int,
        field_name: str,
        old_value,
        new_value,
        change_reason: str,
    ) -> int | None:
        if self.field_history_model._meta.db_table not in self._table_names():
            return None

        row = self.field_history_model.objects.create(
            parent_table=parent_table,
            parent_id=parent_id,
            field_name=field_name,
            old_value=old_value,
            new_value=new_value,
            change_reason=change_reason,
            actor_user_id="system",
            actor_role_code="SYSTEM",
            schema_version=1,
        )
        return int(row.pk)

    @staticmethod
    def _table_names() -> set[str]:
        return set(connection.introspection.table_names())


def cleanup_orphan_attachments(*, now=None, storage_root: str | os.PathLike[str] | None = None) -> AttachmentDeleteResult:
    return OrphanAttachmentCleanupService(storage_root=storage_root).cleanup_orphans(now=now)
