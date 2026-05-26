from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path
import re
from typing import Any
import uuid

from django.core.management.base import BaseCommand, CommandError
from django.db import connections


REPO_ROOT = Path(__file__).resolve().parents[4]
FIXTURES_DIR = REPO_ROOT / "apps" / "safety" / "fixtures"
SEED_DATA_DIR_CANDIDATES = (
    REPO_ROOT / "safety-reference-data",
    REPO_ROOT / "seed-data",
)
SAFE_IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


@dataclass(frozen=True)
class SeedTableSpec:
    table_name: str
    key_columns: tuple[str, ...]
    columns: tuple[str, ...]
    loader_name: str


CSV_HEADER_MAP: dict[str, tuple[str, ...]] = {
    "mscat_taxonomy.csv": (
        "category_id",
        "category_name",
        "subcode_id",
        "subcode_description",
        "cause_type",
    ),
    "immediate_causes.csv": (
        "category_id",
        "category_name",
        "subcode_id",
        "subcode_description",
        "cause_type",
    ),
    "loss_types.csv": (
        "loss_type_id",
        "loss_type_name",
        "description",
    ),
    "soi_checklist_v1.csv": (
        "area_id",
        "area_name",
        "subsection_id",
        "subsection_name",
        "item_number",
        "description",
        "tier",
    ),
}


SEED_TABLE_SPECS: tuple[SeedTableSpec, ...] = (
    SeedTableSpec(
        table_name="master_mscat_taxonomy",
        key_columns=("subcode_id",),
        columns=(
            "category_id",
            "category_name",
            "subcode_id",
            "subcode_description",
            "cause_type",
        ),
        loader_name="load_mscat_taxonomy_rows",
    ),
    SeedTableSpec(
        table_name="master_immediate_causes",
        key_columns=("category_id", "subcode_id"),
        columns=(
            "category_id",
            "category_name",
            "subcode_id",
            "subcode_description",
            "cause_type",
        ),
        loader_name="load_immediate_cause_rows",
    ),
    SeedTableSpec(
        table_name="master_loss_types",
        key_columns=("loss_type_id",),
        columns=("loss_type_id", "loss_type_name", "description"),
        loader_name="load_loss_type_rows",
    ),
    SeedTableSpec(
        table_name="master_soi_area",
        key_columns=("area_id",),
        columns=(
            "area_id",
            "area_name",
            "section_12_flag",
            "display_order",
            "active",
            "seeded_version",
        ),
        loader_name="load_soi_area_rows",
    ),
    SeedTableSpec(
        table_name="master_soi_area_item",
        key_columns=("area_id", "subsection_id", "item_number", "description"),
        columns=(
            "area_id",
            "area_name",
            "subsection_id",
            "subsection_name",
            "item_number",
            "description",
            "tier",
            "active",
            "seeded_version",
            "schema_version",
            "updated_by",
            "updated_date",
        ),
        loader_name="load_soi_area_item_rows",
    ),
    SeedTableSpec(
        table_name="master_soi_checklist_version",
        key_columns=("version_label",),
        columns=(
            "version_label",
            "effective_from",
            "effective_to",
            "source_description",
            "active",
            "created_by",
        ),
        loader_name="load_soi_checklist_version_rows",
    ),
    SeedTableSpec(
        table_name="master_safety_incident_type",
        key_columns=("type_code",),
        columns=("type_code", "type_name", "imo_reportable", "description", "active"),
        loader_name="load_incident_type_rows",
    ),
    SeedTableSpec(
        table_name="master_safety_bias_guard",
        key_columns=("guard_code",),
        columns=(
            "guard_code",
            "guard_name",
            "family",
            "description",
            "bit_position",
            "active",
        ),
        loader_name="load_bias_guard_rows",
    ),
)


def validate_csv_headers(filename: str, actual_headers: list[str] | tuple[str, ...]) -> None:
    expected_headers = CSV_HEADER_MAP[filename]
    if tuple(actual_headers) != expected_headers:
        raise CommandError(
            f"{filename} headers do not match the locked mapping. "
            f"Expected {expected_headers}, got {tuple(actual_headers)}."
        )


def get_seed_data_dir() -> Path:
    for candidate in SEED_DATA_DIR_CANDIDATES:
        if candidate.exists():
            return candidate

    candidate_list = ", ".join(str(path) for path in SEED_DATA_DIR_CANDIDATES)
    raise CommandError(f"Safety seed-data directory not found. Checked: {candidate_list}")


def read_csv_rows(filename: str) -> list[dict[str, str]]:
    seed_file = get_seed_data_dir() / filename
    if not seed_file.exists():
        raise CommandError(f"Required seed CSV not found: {seed_file}")

    with seed_file.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise CommandError(f"{seed_file} is missing a header row.")
        validate_csv_headers(filename, reader.fieldnames)
        return list(reader)


def read_fixture_rows(filename: str) -> list[dict[str, Any]]:
    fixture_path = FIXTURES_DIR / filename
    if not fixture_path.exists():
        raise CommandError(f"Required fixture not found: {fixture_path}")

    with fixture_path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)

    if not isinstance(payload, list):
        raise CommandError(f"{fixture_path} must contain a JSON list of rows.")
    return payload


def _to_int(value: str) -> int:
    return int(value)


def _normalize_item_number(value: str) -> str:
    return value.strip()


def load_mscat_taxonomy_rows() -> list[dict[str, Any]]:
    rows = read_csv_rows("mscat_taxonomy.csv")
    return [
        {
            "category_id": _to_int(row["category_id"]),
            "category_name": row["category_name"],
            "subcode_id": row["subcode_id"],
            "subcode_description": row["subcode_description"],
            "cause_type": row["cause_type"],
        }
        for row in rows
    ]


def load_immediate_cause_rows() -> list[dict[str, Any]]:
    rows = read_csv_rows("immediate_causes.csv")
    return [
        {
            "category_id": _to_int(row["category_id"]),
            "category_name": row["category_name"],
            "subcode_id": row["subcode_id"],
            "subcode_description": row["subcode_description"],
            "cause_type": row["cause_type"],
        }
        for row in rows
    ]


def load_loss_type_rows() -> list[dict[str, Any]]:
    rows = read_csv_rows("loss_types.csv")
    return [
        {
            "loss_type_id": _to_int(row["loss_type_id"]),
            "loss_type_name": row["loss_type_name"],
            "description": row["description"],
        }
        for row in rows
    ]


def load_soi_area_rows() -> list[dict[str, Any]]:
    return read_fixture_rows("master_soi_area.json")


def load_soi_area_item_rows() -> list[dict[str, Any]]:
    rows = read_csv_rows("soi_checklist_v1.csv")
    return [
        {
            "area_id": _to_int(row["area_id"]),
            "area_name": row["area_name"],
            "subsection_id": _to_int(row["subsection_id"]),
            "subsection_name": row["subsection_name"],
            "item_number": _normalize_item_number(row["item_number"]),
            "description": row["description"],
            "tier": row["tier"],
            "active": 1,
            "seeded_version": "v1.0",
            "schema_version": 1,
            "updated_by": None,
            "updated_date": None,
        }
        for row in rows
    ]


def load_soi_checklist_version_rows() -> list[dict[str, Any]]:
    return read_fixture_rows("master_soi_checklist_version.json")


def load_incident_type_rows() -> list[dict[str, Any]]:
    return read_fixture_rows("master_safety_incident_type.json")


def load_bias_guard_rows() -> list[dict[str, Any]]:
    return read_fixture_rows("master_safety_bias_guard.json")


def _validate_identifier(identifier: str) -> str:
    if not SAFE_IDENTIFIER_RE.fullmatch(identifier):
        raise CommandError(f"Unsafe SQL identifier encountered: {identifier}")
    return identifier


def _validate_row_shape(table_name: str, columns: tuple[str, ...], rows: list[dict[str, Any]]) -> None:
    required_columns = set(columns)
    for row in rows:
        missing_columns = required_columns - row.keys()
        if missing_columns:
            missing = ", ".join(sorted(missing_columns))
            raise CommandError(f"{table_name} seed row is missing required columns: {missing}")


def _load_existing_keys(cursor, table_name: str, key_columns: tuple[str, ...]) -> set[tuple[Any, ...]]:
    key_sql = ", ".join(_validate_identifier(column) for column in key_columns)
    cursor.execute(f"SELECT {key_sql} FROM {_validate_identifier(table_name)}")
    return {tuple(row) for row in cursor.fetchall()}


def _insert_row(cursor, table_name: str, columns: tuple[str, ...], row: dict[str, Any]) -> None:
    extra_values = _insert_defaults_for(table_name)
    insert_columns = ("id", "legacy_int_id", *columns, *extra_values.keys())
    column_sql = ", ".join(_validate_identifier(column) for column in insert_columns)
    placeholders = ", ".join(["%s"] * len(insert_columns))
    cursor.execute(f"SELECT COALESCE(MAX(legacy_int_id), 0) + 1 FROM {_validate_identifier(table_name)}")
    next_legacy_id = cursor.fetchone()[0]
    values = [uuid.uuid4().hex, next_legacy_id, *[row[column] for column in columns], *extra_values.values()]
    cursor.execute(
        f"INSERT INTO {_validate_identifier(table_name)} ({column_sql}) VALUES ({placeholders})",
        values,
    )


def _insert_defaults_for(table_name: str) -> dict[str, Any]:
    if table_name == "master_mscat_taxonomy":
        return {"active": 1, "seeded_version": "v1.0-Round21", "schema_version": 1}
    if table_name == "master_immediate_causes":
        return {"active": 1, "seeded_version": "v1.0", "schema_version": 1}
    if table_name == "master_loss_types":
        return {"active": 1, "seeded_version": "v1.0"}
    return {}


def _update_row(
    cursor,
    table_name: str,
    key_columns: tuple[str, ...],
    columns: tuple[str, ...],
    row: dict[str, Any],
) -> None:
    non_key_columns = [column for column in columns if column not in key_columns]
    if not non_key_columns:
        return

    set_sql = ", ".join(f"{_validate_identifier(column)} = %s" for column in non_key_columns)
    where_sql = " AND ".join(f"{_validate_identifier(column)} = %s" for column in key_columns)
    values = [row[column] for column in non_key_columns] + [row[column] for column in key_columns]
    cursor.execute(
        f"UPDATE {_validate_identifier(table_name)} SET {set_sql} WHERE {where_sql}",
        values,
    )


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

    return {
        "inserted": inserted,
        "updated": updated,
        "total": len(rows),
    }


def seed_master_safety(*, using: str = "default", stdout=None) -> dict[str, dict[str, int]]:
    connection = connections[using]
    summary: dict[str, dict[str, int]] = {}

    with connection.cursor() as cursor:
        for spec in SEED_TABLE_SPECS:
            loader = globals()[spec.loader_name]
            rows = loader()
            result = upsert_rows(
                cursor=cursor,
                table_name=spec.table_name,
                key_columns=spec.key_columns,
                columns=spec.columns,
                rows=rows,
            )
            summary[spec.table_name] = result
            if stdout is not None:
                stdout.write(
                    f"{spec.table_name}: inserted={result['inserted']} "
                    f"updated={result['updated']} total={result['total']}"
                )

    return summary


class Command(BaseCommand):
    help = "Seed the Safety master reference tables from seed-data CSVs and JSON fixtures."

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--database",
            default="default",
            help="Database alias to seed. Defaults to 'default'.",
        )

    def handle(self, *args, **options):
        database_alias = options["database"]
        try:
            seed_master_safety(using=database_alias, stdout=self.stdout)
        except CommandError:
            raise
        except Exception as exc:
            raise CommandError(str(exc)) from exc
