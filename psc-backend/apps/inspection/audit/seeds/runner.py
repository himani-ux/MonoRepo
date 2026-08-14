from __future__ import annotations

import csv
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from django.core.management.base import CommandError
from django.db import connections, transaction


IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


@dataclass(frozen=True)
class SeedTableSpec:
    csv_name: str
    table_name: str
    source_columns: tuple[str, ...]
    target_columns: tuple[str, ...]
    key_columns: tuple[str, ...]
    int_columns: frozenset[str] = field(default_factory=frozenset)
    bool_columns: frozenset[str] = field(default_factory=frozenset)
    nullable_columns: frozenset[str] = field(default_factory=frozenset)
    resolve_checklist_code: bool = False


SEED_TABLE_SPECS: tuple[SeedTableSpec, ...] = (
    SeedTableSpec(
        csv_name="master_audit_classification.csv",
        table_name="master_audit_classification",
        source_columns=("classification_code", "display_name", "is_active"),
        target_columns=("classification_code", "display_name", "is_active"),
        key_columns=("classification_code",),
        bool_columns=frozenset({"is_active"}),
    ),
    SeedTableSpec(
        csv_name="master_audit_finding_category.csv",
        table_name="master_audit_finding_category",
        source_columns=("category_code", "display_name", "default_target_days"),
        target_columns=("category_code", "display_name", "default_target_days"),
        key_columns=("category_code",),
        int_columns=frozenset({"default_target_days"}),
        nullable_columns=frozenset({"default_target_days"}),
    ),
    SeedTableSpec(
        csv_name="master_audit_area.csv",
        table_name="master_audit_area",
        source_columns=("area_code", "display_name", "is_vessel_only", "sequence_no"),
        target_columns=("area_code", "display_name", "is_vessel_only", "sequence_no"),
        key_columns=("area_code",),
        int_columns=frozenset({"sequence_no"}),
        bool_columns=frozenset({"is_vessel_only"}),
    ),
    SeedTableSpec(
        csv_name="master_audit_window_rule.csv",
        table_name="master_audit_window_rule",
        source_columns=(
            "standard_code",
            "subtype_code",
            "window_open_offset_months",
            "window_close_offset_months",
            "cadence_months",
            "regulatory_citation",
            "is_active",
        ),
        target_columns=(
            "standard_code",
            "subtype_code",
            "window_open_offset_months",
            "window_close_offset_months",
            "cadence_months",
            "regulatory_citation",
            "is_active",
        ),
        key_columns=("standard_code", "subtype_code"),
        int_columns=frozenset({"window_open_offset_months", "window_close_offset_months", "cadence_months"}),
        bool_columns=frozenset({"is_active"}),
    ),
    SeedTableSpec(
        csv_name="master_audit_subtype.csv",
        table_name="master_audit_subtype",
        source_columns=("classification_code", "subtype_code", "display_name", "is_external", "is_active"),
        target_columns=("classification_code", "subtype_code", "display_name", "is_external", "is_active"),
        key_columns=("classification_code", "subtype_code"),
        bool_columns=frozenset({"is_external", "is_active"}),
    ),
    SeedTableSpec(
        csv_name="master_audit_checklist.csv",
        table_name="master_audit_checklist",
        source_columns=(
            "checklist_code",
            "name",
            "auditee_type",
            "scope_dept",
            "ship_type_scope",
            "source_form_ref",
            "code_version",
            "is_active",
        ),
        target_columns=(
            "checklist_code",
            "name",
            "auditee_type",
            "scope_dept",
            "ship_type_scope",
            "source_form_ref",
            "code_version",
            "is_active",
        ),
        key_columns=("checklist_code",),
        bool_columns=frozenset({"is_active"}),
        nullable_columns=frozenset({"scope_dept", "ship_type_scope", "code_version"}),
    ),
    SeedTableSpec(
        csv_name="master_audit_checklist_item.csv",
        table_name="master_audit_checklist_item",
        source_columns=(
            "checklist_code",
            "location_code",
            "item_code",
            "question",
            "guideline",
            "regulation_ref",
            "ksm_sms_ref",
            "ship_type",
            "sequence_no",
        ),
        target_columns=(
            "master_audit_checklist_id",
            "location_code",
            "item_code",
            "question",
            "guideline",
            "regulation_ref",
            "ksm_sms_ref",
            "ship_type",
            "sequence_no",
        ),
        key_columns=("master_audit_checklist_id", "item_code", "sequence_no"),
        int_columns=frozenset({"sequence_no"}),
        nullable_columns=frozenset({"location_code", "guideline", "regulation_ref", "ksm_sms_ref", "ship_type"}),
        resolve_checklist_code=True,
    ),
    SeedTableSpec(
        csv_name="master_ism_clause.csv",
        table_name="master_ism_clause",
        source_columns=("clause_no", "clause_text", "section_no", "code_version"),
        target_columns=("clause_no", "clause_text", "section_no", "code_version"),
        key_columns=("clause_no", "code_version"),
        nullable_columns=frozenset({"section_no"}),
    ),
    SeedTableSpec(
        csv_name="master_isps_clause.csv",
        table_name="master_isps_clause",
        source_columns=("section_no", "section_title", "section_text", "code_version"),
        target_columns=("section_no", "section_title", "section_text", "code_version"),
        key_columns=("section_no", "code_version"),
        nullable_columns=frozenset({"section_text"}),
    ),
    SeedTableSpec(
        csv_name="master_mlc_title.csv",
        table_name="master_mlc_title",
        source_columns=("title_no", "regulation_no", "standard_a_code", "title_text", "code_version"),
        target_columns=("title_no", "regulation_no", "standard_a_code", "title_text", "code_version"),
        key_columns=("title_no", "regulation_no", "standard_a_code", "code_version"),
        nullable_columns=frozenset({"regulation_no", "standard_a_code"}),
    ),
    SeedTableSpec(
        csv_name="master_solas_chapter.csv",
        table_name="master_solas_chapter",
        source_columns=("chapter_no", "regulation_no", "title", "code_version"),
        target_columns=("chapter_no", "regulation_no", "title", "code_version"),
        key_columns=("chapter_no", "regulation_no", "code_version"),
        nullable_columns=frozenset({"regulation_no"}),
    ),
    SeedTableSpec(
        csv_name="master_stcw_section.csv",
        table_name="master_stcw_section",
        source_columns=("section_no", "title", "code_version"),
        target_columns=("section_no", "title", "code_version"),
        key_columns=("section_no", "code_version"),
    ),
    SeedTableSpec(
        csv_name="master_marpol_annex.csv",
        table_name="master_marpol_annex",
        source_columns=("annex_no", "regulation_no", "title", "code_version"),
        target_columns=("annex_no", "regulation_no", "title", "code_version"),
        key_columns=("annex_no", "regulation_no", "code_version"),
        nullable_columns=frozenset({"regulation_no"}),
    ),
    SeedTableSpec(
        csv_name="master_colreg_rule.csv",
        table_name="master_colreg_rule",
        source_columns=("rule_no", "title", "code_version"),
        target_columns=("rule_no", "title", "code_version"),
        key_columns=("rule_no", "code_version"),
    ),
    SeedTableSpec(
        csv_name="master_ksm_sms_chapter.csv",
        table_name="master_ksm_sms_chapter",
        source_columns=("chapter_code", "chapter_name"),
        target_columns=("chapter_code", "chapter_name"),
        key_columns=("chapter_code",),
    ),
    SeedTableSpec(
        csv_name="master_rca_template.csv",
        table_name="master_rca_template",
        source_columns=(
            "category",
            "title",
            "template_text",
            "example_evidence_hint",
            "applicable_def_categories",
            "code_version",
            "is_active",
        ),
        target_columns=(
            "category",
            "title",
            "template_text",
            "example_evidence_hint",
            "applicable_def_categories",
            "code_version",
            "is_active",
        ),
        key_columns=("category", "title", "code_version"),
        bool_columns=frozenset({"is_active"}),
        nullable_columns=frozenset({"example_evidence_hint", "applicable_def_categories", "code_version"}),
    ),
    SeedTableSpec(
        csv_name="master_external_auditor_category_map.csv",
        table_name="master_external_auditor_category_map",
        source_columns=("free_text_pattern", "canonical_iacs_code"),
        target_columns=("free_text_pattern", "canonical_iacs_code"),
        key_columns=("free_text_pattern", "canonical_iacs_code"),
    ),
)


def resolve_seed_dir(seed_dir: str | Path | None = None) -> Path:
    if seed_dir is not None:
        path = Path(seed_dir).expanduser().resolve()
        if not path.is_dir():
            raise CommandError(f"Audit seed directory does not exist: {path}")
        return path

    candidates: list[Path] = []
    cwd = Path.cwd().resolve()
    for base in (cwd, *cwd.parents):
        candidates.append(base / "docs" / "seeds")

    module_path = Path(__file__).resolve()
    for parent in module_path.parents:
        candidates.append(parent / "docs" / "seeds")

    seen: set[Path] = set()
    for candidate in candidates:
        if candidate in seen:
            continue
        seen.add(candidate)
        if candidate.is_dir():
            return candidate

    raise CommandError("Could not locate docs/seeds. Pass --seed-dir explicitly.")


def read_seed_rows(
    spec: SeedTableSpec,
    seed_dir: str | Path,
    *,
    checklist_ids: dict[str, Any] | None = None,
    checklist_codes: set[str] | None = None,
) -> list[dict[str, Any]]:
    csv_path = Path(seed_dir) / spec.csv_name
    if not csv_path.is_file():
        raise CommandError(f"Missing Audit seed CSV: {csv_path}")

    with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        _validate_headers(spec, reader.fieldnames)
        rows = [
            _coerce_csv_row(
                spec,
                line_number=line_number,
                csv_row=row,
                checklist_ids=checklist_ids,
                checklist_codes=checklist_codes,
            )
            for line_number, row in enumerate(reader, start=2)
        ]

    _validate_duplicate_seed_keys(spec, rows)
    return rows


def seed_audit_masters(
    *,
    using: str = "default",
    seed_dir: str | Path | None = None,
    dry_run: bool = False,
    stdout=None,
) -> dict[str, dict[str, int]]:
    resolved_seed_dir = resolve_seed_dir(seed_dir)
    summary: dict[str, dict[str, int]] = {}

    if dry_run:
        checklist_codes: set[str] = set()
        for spec in SEED_TABLE_SPECS:
            rows = read_seed_rows(spec, resolved_seed_dir, checklist_codes=checklist_codes)
            if spec.table_name == "master_audit_checklist":
                checklist_codes = {row["checklist_code"] for row in rows}
            summary[spec.table_name] = {"inserted": 0, "updated": 0, "total": len(rows)}
            _write_summary(stdout, spec.table_name, summary[spec.table_name], dry_run=True)
        return summary

    connection = connections[using]
    with transaction.atomic(using=using):
        with connection.cursor() as cursor:
            checklist_ids: dict[str, Any] = {}
            for spec in SEED_TABLE_SPECS:
                if spec.resolve_checklist_code:
                    checklist_ids = _load_checklist_ids(cursor)

                rows = read_seed_rows(spec, resolved_seed_dir, checklist_ids=checklist_ids)
                result = upsert_rows(
                    cursor=cursor,
                    table_name=spec.table_name,
                    key_columns=spec.key_columns,
                    columns=spec.target_columns,
                    rows=rows,
                )
                summary[spec.table_name] = result
                _write_summary(stdout, spec.table_name, result, dry_run=False)

    return summary


def upsert_rows(
    *,
    cursor,
    table_name: str,
    key_columns: tuple[str, ...],
    columns: tuple[str, ...],
    rows: list[dict[str, Any]],
) -> dict[str, int]:
    _validate_row_shape(table_name, columns, rows)
    existing_keys = _load_existing_keys(cursor, table_name, key_columns)

    inserted = 0
    updated = 0
    for row in rows:
        row_key = tuple(row[column] for column in key_columns)
        if row_key in existing_keys:
            _update_row(cursor, table_name, key_columns, columns, row)
            updated += 1
        else:
            _insert_row(cursor, table_name, columns, row)
            existing_keys.add(row_key)
            inserted += 1

    return {"inserted": inserted, "updated": updated, "total": len(rows)}


def _validate_headers(spec: SeedTableSpec, fieldnames: list[str] | None) -> None:
    if fieldnames is None:
        raise CommandError(f"{spec.csv_name} is empty or has no header row")

    actual = tuple(fieldnames)
    expected = spec.source_columns
    if actual != expected:
        raise CommandError(
            f"{spec.csv_name} header mismatch. Expected {', '.join(expected)}; got {', '.join(actual)}"
        )


def _coerce_csv_row(
    spec: SeedTableSpec,
    *,
    line_number: int,
    csv_row: dict[str, str],
    checklist_ids: dict[str, Any] | None,
    checklist_codes: set[str] | None,
) -> dict[str, Any]:
    row: dict[str, Any] = {}
    for source_column, target_column in zip(spec.source_columns, spec.target_columns, strict=True):
        if spec.resolve_checklist_code and source_column == "checklist_code":
            checklist_code = _coerce_text(csv_row.get(source_column))
            row[target_column] = _resolve_checklist_id(
                checklist_code,
                checklist_ids=checklist_ids,
                checklist_codes=checklist_codes,
                csv_name=spec.csv_name,
                line_number=line_number,
            )
            continue

        row[target_column] = _coerce_value(
            spec,
            column=target_column,
            value=csv_row.get(source_column),
            line_number=line_number,
        )

    return row


def _coerce_value(spec: SeedTableSpec, *, column: str, value: str | None, line_number: int) -> Any:
    text = _coerce_text(value)
    if text == "":
        if column in spec.nullable_columns:
            return None
        raise CommandError(f"{spec.csv_name}:{line_number} has a blank required value for {column}")

    if column in spec.bool_columns:
        return _coerce_bool(spec, column=column, value=text, line_number=line_number)
    if column in spec.int_columns:
        return _coerce_int(spec, column=column, value=text, line_number=line_number)
    return text


def _coerce_text(value: str | None) -> str:
    if value is None:
        return ""
    return value.strip()


def _coerce_bool(spec: SeedTableSpec, *, column: str, value: str, line_number: int) -> bool:
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "y"}:
        return True
    if normalized in {"0", "false", "no", "n"}:
        return False
    raise CommandError(f"{spec.csv_name}:{line_number} has invalid boolean for {column}: {value}")


def _coerce_int(spec: SeedTableSpec, *, column: str, value: str, line_number: int) -> int:
    try:
        return int(value)
    except ValueError as exc:
        raise CommandError(f"{spec.csv_name}:{line_number} has invalid integer for {column}: {value}") from exc


def _resolve_checklist_id(
    checklist_code: str,
    *,
    checklist_ids: dict[str, Any] | None,
    checklist_codes: set[str] | None,
    csv_name: str,
    line_number: int,
) -> Any:
    if checklist_ids is not None:
        try:
            return checklist_ids[checklist_code]
        except KeyError as exc:
            raise CommandError(f"{csv_name}:{line_number} references unknown checklist_code {checklist_code}") from exc

    if checklist_codes is not None and checklist_code in checklist_codes:
        return f"DRY_RUN:{checklist_code}"

    raise CommandError(f"{csv_name}:{line_number} references unknown checklist_code {checklist_code}")


def _validate_duplicate_seed_keys(spec: SeedTableSpec, rows: list[dict[str, Any]]) -> None:
    seen: set[tuple[Any, ...]] = set()
    for row in rows:
        row_key = tuple(row[column] for column in spec.key_columns)
        if row_key in seen:
            key_text = ", ".join(str(part) for part in row_key)
            raise CommandError(f"{spec.csv_name} contains duplicate natural key: {key_text}")
        seen.add(row_key)


def _validate_row_shape(table_name: str, columns: tuple[str, ...], rows: list[dict[str, Any]]) -> None:
    expected = set(columns)
    for index, row in enumerate(rows, start=1):
        actual = set(row)
        if actual != expected:
            raise CommandError(
                f"{table_name} row {index} has columns {sorted(actual)}; expected {sorted(expected)}"
            )


def _load_existing_keys(cursor, table_name: str, key_columns: tuple[str, ...]) -> set[tuple[Any, ...]]:
    columns_sql = ", ".join(_quote_identifier(column) for column in key_columns)
    cursor.execute(f"SELECT {columns_sql} FROM {_quote_identifier(table_name)}")  # nosec B608
    return {tuple(row) for row in cursor.fetchall()}


def _load_checklist_ids(cursor) -> dict[str, Any]:
    cursor.execute("SELECT [checklist_code], [id] FROM [master_audit_checklist]")
    return {checklist_code: checklist_id for checklist_code, checklist_id in cursor.fetchall()}


def _insert_row(cursor, table_name: str, columns: tuple[str, ...], row: dict[str, Any]) -> None:
    columns_sql = ", ".join(_quote_identifier(column) for column in columns)
    placeholders = ", ".join(["%s"] * len(columns))
    values = [row[column] for column in columns]
    cursor.execute(f"INSERT INTO {_quote_identifier(table_name)} ({columns_sql}) VALUES ({placeholders})", values)  # nosec B608


def _update_row(
    cursor,
    table_name: str,
    key_columns: tuple[str, ...],
    columns: tuple[str, ...],
    row: dict[str, Any],
) -> None:
    non_key_columns = tuple(column for column in columns if column not in key_columns)
    if not non_key_columns:
        return

    set_sql = ", ".join(f"{_quote_identifier(column)} = %s" for column in non_key_columns)
    where_sql = " AND ".join(f"{_quote_identifier(column)} = %s" for column in key_columns)
    values = [row[column] for column in non_key_columns] + [row[column] for column in key_columns]
    cursor.execute(f"UPDATE {_quote_identifier(table_name)} SET {set_sql} WHERE {where_sql}", values)  # nosec B608


def _quote_identifier(identifier: str) -> str:
    if not IDENTIFIER_RE.match(identifier):
        raise CommandError(f"Unsafe SQL identifier: {identifier}")
    return f"[{identifier}]"


def _write_summary(stdout, table_name: str, result: dict[str, int], *, dry_run: bool) -> None:
    if stdout is None:
        return

    prefix = "dry-run " if dry_run else ""
    stdout.write(
        f"{prefix}{table_name}: inserted={result['inserted']} "
        f"updated={result['updated']} total={result['total']}"
    )
