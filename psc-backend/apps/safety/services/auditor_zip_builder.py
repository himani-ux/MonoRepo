from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import date, datetime
from io import BytesIO
import os
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from PyPDF2 import PdfReader
from django.db.models import Q
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from apps.safety.authentication.vessel_scope import filter_by_vessel_scope
from apps.safety.models import EvidenceItem, Incident, SCMMeeting, SafetyFieldHistory, SOIFinding, SOIInspection

from .pdf_renderer import IncidentPdfRenderer, NearMissLightweightPdfRenderer, SCMLegacyPdfRenderer, SOISummaryPdfRenderer


@dataclass(frozen=True)
class AuditorBundleIncludedRecord:
    record_type: str
    record_id: str
    reference: str
    vessel_id: str
    pdf_file_name: str
    attachment_archive_paths: list[str]


@dataclass(frozen=True)
class AuditorZipBuildResult:
    content: bytes
    content_type: str
    export_path: str | None
    file_name: str
    record_count: int
    attachment_count: int
    record_types: tuple[str, ...]
    included_records: list[AuditorBundleIncludedRecord]
    missing_attachment_paths: list[str]


class AuditorZipBuilder:
    content_type = "application/zip"

    INCIDENT = "INCIDENT"
    NEAR_MISS = "NEAR_MISS"
    SCM = "SCM"
    SOI = "SOI"

    VALID_RECORD_TYPES = (INCIDENT, NEAR_MISS, SCM, SOI)
    _PATH_HINT_TOKENS = ("attachment", "path", "file", "scan", "photo", "evidence")
    _IGNORED_EXPORT_HISTORY_FIELDS = {
        "incident_pdf_export",
        "near_miss_pdf_export",
        "scm_pdf_export",
        "soi_summary_pdf_export",
        "incident_msc_mepc3_export",
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

    def __init__(
        self,
        *,
        incident_model=Incident,
        scm_model=SCMMeeting,
        soi_model=SOIInspection,
        soi_finding_model=SOIFinding,
        field_history_model=SafetyFieldHistory,
        evidence_item_model=EvidenceItem,
        incident_pdf_renderer_class=IncidentPdfRenderer,
        near_miss_pdf_renderer_class=NearMissLightweightPdfRenderer,
        scm_pdf_renderer_class=SCMLegacyPdfRenderer,
        soi_pdf_renderer_class=SOISummaryPdfRenderer,
        export_root: str | os.PathLike[str] | None = None,
    ) -> None:
        self.incident_model = incident_model
        self.scm_model = scm_model
        self.soi_model = soi_model
        self.soi_finding_model = soi_finding_model
        self.field_history_model = field_history_model
        self.evidence_item_model = evidence_item_model
        self.incident_pdf_renderer = incident_pdf_renderer_class()
        self.near_miss_pdf_renderer = near_miss_pdf_renderer_class()
        self.scm_pdf_renderer = scm_pdf_renderer_class()
        self.soi_pdf_renderer = soi_pdf_renderer_class()
        default_root = Path.cwd() / "var" / "www" / "ksm_uploads" / "safety"
        self.export_root = Path(export_root or os.getenv("SAFETY_EXPORT_ROOT") or default_root)

    def build_bundle(
        self,
        *,
        record_types: Sequence[str],
        date_from: date | str,
        date_to: date | str,
        viewer_user,
        vessel_id: str | None = None,
        persist: bool = True,
    ) -> AuditorZipBuildResult:
        normalized_record_types = self._normalize_record_types(record_types)
        start_date = self._coerce_date(date_from, field_name="date_from")
        end_date = self._coerce_date(date_to, field_name="date_to")
        if end_date < start_date:
            raise ValidationError({"date_to": "date_to must be greater than or equal to date_from."})

        candidate_records = self._collect_candidate_records(
            viewer_user=viewer_user,
            record_types=normalized_record_types,
            start_date=start_date,
            end_date=end_date,
            vessel_id=vessel_id,
        )
        if not candidate_records:
            raise ValidationError("No exportable Safety records matched the selected date range.")

        used_pdf_names: set[str] = set()
        used_attachment_names: set[str] = set()
        included_records: list[AuditorBundleIncludedRecord] = []
        missing_attachment_paths: list[str] = []
        attachment_count = 0

        buffer = BytesIO()
        with ZipFile(buffer, "w", compression=ZIP_DEFLATED) as archive:
            for record_type, record in candidate_records:
                render_result = self._render_pdf(record_type=record_type, record=record, viewer_user=viewer_user)
                self._validate_pdf_content(render_result.content)

                pdf_file_name = self._ensure_unique_name(render_result.file_name, used_names=used_pdf_names)
                archive.writestr(pdf_file_name, render_result.content)

                attachment_archive_paths: list[str] = []
                for attachment_path in self._collect_attachment_paths(record_type=record_type, record=record):
                    resolved_path = self._resolve_attachment_path(attachment_path)
                    if resolved_path is None or not resolved_path.is_file():
                        missing_attachment_paths.append(str(attachment_path))
                        continue

                    archive_path = self._build_attachment_archive_path(
                        record_type=record_type,
                        record=record,
                        attachment_path=resolved_path,
                        used_names=used_attachment_names,
                    )
                    archive.write(resolved_path, archive_path)
                    attachment_archive_paths.append(archive_path)
                    attachment_count += 1

                included_records.append(
                    AuditorBundleIncludedRecord(
                        record_type=record_type,
                        record_id=str(record.pk),
                        reference=self._record_reference(record_type, record),
                        vessel_id=str(getattr(record, "vessel_id", "")),
                        pdf_file_name=pdf_file_name,
                        attachment_archive_paths=attachment_archive_paths,
                    )
                )

        content = buffer.getvalue()
        export_path = self._persist_bundle(
            content=content,
            included_records=included_records,
            start_date=start_date,
            end_date=end_date,
        ) if persist else None

        return AuditorZipBuildResult(
            content=content,
            content_type=self.content_type,
            export_path=export_path,
            file_name=self._build_bundle_file_name(start_date=start_date, end_date=end_date),
            record_count=len(included_records),
            attachment_count=attachment_count,
            record_types=normalized_record_types,
            included_records=included_records,
            missing_attachment_paths=missing_attachment_paths,
        )

    def _normalize_record_types(self, record_types: Sequence[str]) -> tuple[str, ...]:
        normalized: list[str] = []
        for record_type in record_types:
            value = str(record_type or "").strip().upper()
            if value and value not in normalized:
                normalized.append(value)
        if not normalized:
            raise ValidationError({"record_types": "Select at least one record type."})

        unsupported = [value for value in normalized if value not in self.VALID_RECORD_TYPES]
        if unsupported:
            raise ValidationError({"record_types": f"Unsupported record type(s): {', '.join(unsupported)}."})
        return tuple(normalized)

    def _coerce_date(self, value: date | str, *, field_name: str) -> date:
        if isinstance(value, date) and not isinstance(value, datetime):
            return value
        try:
            return date.fromisoformat(str(value))
        except ValueError as exc:
            raise ValidationError({field_name: "Enter a valid date in YYYY-MM-DD format."}) from exc

    def _collect_candidate_records(
        self,
        *,
        viewer_user,
        record_types: Sequence[str],
        start_date: date,
        end_date: date,
        vessel_id: str | None,
    ) -> list[tuple[str, object]]:
        selected_vessel = None if vessel_id in (None, "") else str(vessel_id)
        collected: list[tuple[str, object]] = []

        if self.INCIDENT in record_types:
            queryset = self.incident_model.objects.filter(
                is_deleted=False,
                record_type=Incident.RecordType.INCIDENT,
            ).filter(
                Q(current_phase__gte=7) | Q(state__in={"APPROVED", "CLOSED"})
            )
            queryset = filter_by_vessel_scope(queryset, viewer_user)
            queryset = queryset.filter(occurred_at__date__gte=start_date, occurred_at__date__lte=end_date)
            if selected_vessel is not None:
                queryset = queryset.filter(vessel_id=selected_vessel)
            collected.extend((self.INCIDENT, row) for row in queryset.order_by("occurred_at", "id"))

        if self.NEAR_MISS in record_types:
            queryset = self.incident_model.objects.filter(
                is_deleted=False,
                record_type=Incident.RecordType.NEAR_MISS,
            )
            queryset = filter_by_vessel_scope(queryset, viewer_user)
            queryset = queryset.filter(occurred_at__date__gte=start_date, occurred_at__date__lte=end_date)
            if selected_vessel is not None:
                queryset = queryset.filter(vessel_id=selected_vessel)
            collected.extend((self.NEAR_MISS, row) for row in queryset.order_by("occurred_at", "id"))

        if self.SCM in record_types:
            queryset = self.scm_model.objects.filter(
                is_deleted=False,
                state=SCMMeeting.State.SIGNED_OFF,
                master_signed_off_at__isnull=False,
                meeting_date__gte=start_date,
                meeting_date__lte=end_date,
            )
            queryset = filter_by_vessel_scope(queryset, viewer_user)
            if selected_vessel is not None:
                queryset = queryset.filter(vessel_id=selected_vessel)
            collected.extend((self.SCM, row) for row in queryset.order_by("meeting_date", "id"))

        if self.SOI in record_types:
            queryset = self.soi_model.objects.filter(
                is_deleted=False,
                state__in={SOIInspection.State.REPORTED, SOIInspection.State.CLOSED},
                reported_at__isnull=False,
            ).exclude(checklist_unique_id__in=(None, ""))
            queryset = filter_by_vessel_scope(queryset, viewer_user)
            queryset = queryset.filter(reported_at__date__gte=start_date, reported_at__date__lte=end_date)
            if selected_vessel is not None:
                queryset = queryset.filter(vessel_id=selected_vessel)
            collected.extend((self.SOI, row) for row in queryset.order_by("reported_at", "id"))

        return collected

    def _render_pdf(self, *, record_type: str, record, viewer_user):
        if record_type == self.INCIDENT:
            return self.incident_pdf_renderer.render_incident_pdf(
                incident_id=record.pk,
                viewer_user=viewer_user,
                persist=True,
            )
        if record_type == self.NEAR_MISS:
            return self.near_miss_pdf_renderer.render_near_miss_pdf(
                incident_id=record.pk,
                viewer_user=viewer_user,
                persist=True,
            )
        if record_type == self.SCM:
            return self.scm_pdf_renderer.render_scm_pdf(
                meeting_id=record.pk,
                viewer_user=viewer_user,
                persist=True,
            )
        if record_type == self.SOI:
            return self.soi_pdf_renderer.render_soi_pdf(
                inspection_id=record.pk,
                viewer_user=viewer_user,
                persist=True,
            )
        raise ValidationError(f"Unsupported record type: {record_type}.")

    def _collect_attachment_paths(self, *, record_type: str, record) -> list[str]:
        collected: list[str] = []

        if record_type in {self.INCIDENT, self.NEAR_MISS}:
            evidence_items = self.evidence_item_model.objects.filter(incident_id=record.pk).order_by("id")
            for evidence_item in evidence_items:
                collected.extend(self._extract_paths_from_json(evidence_item.metadata_json))

        if record_type == self.SOI:
            findings = self.soi_finding_model.objects.filter(inspection_id=record.pk, is_deleted=False).order_by("id")
            for finding in findings:
                if finding.photo_attachment_path:
                    collected.append(str(finding.photo_attachment_path))

        collected.extend(self._extract_paths_from_field_history(parent_table=record._meta.db_table, parent_id=record.pk))

        seen: set[str] = set()
        deduped: list[str] = []
        for value in collected:
            normalized = str(value).strip()
            if not normalized or normalized in seen:
                continue
            seen.add(normalized)
            deduped.append(normalized)
        return deduped

    def _extract_paths_from_field_history(self, *, parent_table: str, parent_id: int) -> list[str]:
        rows = self.field_history_model.objects.filter(parent_table=parent_table, parent_id=parent_id).order_by("id")
        extracted: list[str] = []
        for row in rows:
            if str(getattr(row, "field_name", "")).strip().lower() in self._IGNORED_EXPORT_HISTORY_FIELDS:
                continue
            for payload in (row.old_value, row.new_value):
                if payload in (None, ""):
                    continue
                try:
                    parsed = __import__("json").loads(payload)
                except Exception:
                    continue
                extracted.extend(self._extract_paths_from_json(parsed))
        return extracted

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
        return "/" in value or "\\" in value or len(candidate.parts) > 1

    def _resolve_attachment_path(self, value: str) -> Path | None:
        candidate = Path(str(value).strip())
        if not candidate.name:
            return None
        if candidate.is_absolute():
            return candidate
        return (Path.cwd() / candidate).resolve(strict=False)

    def _build_attachment_archive_path(self, *, record_type: str, record, attachment_path: Path, used_names: set[str]) -> str:
        reference = self._safe_reference(self._record_reference(record_type, record))
        base_path = f"attachments/{record_type.lower()}/{reference}/{attachment_path.name}"
        return self._ensure_unique_name(base_path, used_names=used_names)

    def _record_reference(self, record_type: str, record) -> str:
        if record_type in {self.INCIDENT, self.NEAR_MISS}:
            return str(record.incident_number)
        if record_type == self.SCM:
            return str(record.scm_number)
        if record_type == self.SOI:
            return str(record.inspection_reference)
        return str(record.pk)

    def _safe_reference(self, value: str) -> str:
        safe = "".join(char if char.isalnum() or char in {"-", "_"} else "-" for char in str(value))
        while "--" in safe:
            safe = safe.replace("--", "-")
        return safe.strip("-") or "record"

    def _ensure_unique_name(self, candidate: str, *, used_names: set[str]) -> str:
        if candidate not in used_names:
            used_names.add(candidate)
            return candidate

        path = Path(candidate)
        stem = path.stem
        suffix = path.suffix
        parent = "" if str(path.parent) == "." else f"{path.parent.as_posix()}/"
        counter = 2
        while True:
            next_candidate = f"{parent}{stem}-{counter}{suffix}"
            if next_candidate not in used_names:
                used_names.add(next_candidate)
                return next_candidate
            counter += 1

    def _validate_pdf_content(self, content: bytes) -> None:
        reader = PdfReader(BytesIO(content))
        if len(reader.pages) < 1:
            raise ValidationError("Generated PDF bundle member contained no pages.")

    def _persist_bundle(
        self,
        *,
        content: bytes,
        included_records: Sequence[AuditorBundleIncludedRecord],
        start_date: date,
        end_date: date,
    ) -> str:
        vessel_ids = {row.vessel_id for row in included_records if row.vessel_id}
        scope = next(iter(vessel_ids)) if len(vessel_ids) == 1 else "fleet"
        export_dir = self.export_root / scope / "exports"
        export_dir.mkdir(parents=True, exist_ok=True)
        output_path = export_dir / self._build_bundle_file_name(start_date=start_date, end_date=end_date)
        output_path.write_bytes(content)
        return str(output_path.resolve())

    @staticmethod
    def _build_bundle_file_name(*, start_date: date, end_date: date) -> str:
        timestamp = timezone.now().strftime("%Y%m%d-%H%M%S")
        return f"safety-auditor-bundle-{start_date:%Y%m%d}-{end_date:%Y%m%d}-{timestamp}.zip"
