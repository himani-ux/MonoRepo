from __future__ import annotations

import csv
from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

from apps.certs.catalog_section_seed import CATALOG_SECTIONS


VALIDITY_TYPES = {"full", "conditional", "short_term", "permanent"}
ISSUING_AUTHORITY_TYPES = {"flag", "class", "RO", "manufacturer", "company", "ko_other"}
SUBMISSION_SCOPES = {"master_only", "all_ranks_with_approval"}
APPLICABILITY_MODES = {"all_matching_type", "specific_vessel_ids"}
SHIP_TYPES = {"all", "bulk_carrier", "tanker", "container", "gas_carrier", "chemical_tanker"}

REQUIRED_CSV_COLUMNS = {
    "canonical_code",
    "section_id",
    "display_name",
    "print_section_label",
    "validity_type",
    "issuing_authority_type",
    "submission_scope",
    "print_order",
}

OPTIONAL_CSV_COLUMNS = {
    "short_name",
    "cadence_months",
    "cadence_custom_days",
    "is_class_tracked",
    "parent_canonical_code",
    "relationship_type_default",
    "applicable_ship_types",
    "mandatory_for_all_vessels",
    "applicability_mode",
    "specific_vessel_ids",
    "parent_supports_dynamic_children",
    "age_gate_max_years",
    "retain_all_versions",
    "linked_pms_component_id",
    "alert_lead_overrides",
    "regulatory_anchor",
    "legacy_remarks",
    "is_active",
}

SECTION_LOOKUP = {
    section.section_id: (section.section_code, section.display_name)
    for section in CATALOG_SECTIONS
}


@dataclass(frozen=True)
class CatalogWorkshopSeedRow:
    canonical_code: str
    section_id: int
    display_name: str
    short_name: str | None
    print_section_label: str
    validity_type: str
    cadence_months: int | None
    cadence_custom_days: int | None
    issuing_authority_type: str
    is_class_tracked: bool
    submission_scope: str
    parent_canonical_code: str | None
    relationship_type_default: str | None
    applicable_ship_types: tuple[str, ...]
    mandatory_for_all_vessels: bool
    applicability_mode: str
    specific_vessel_ids: tuple[str, ...]
    parent_supports_dynamic_children: bool
    age_gate_max_years: int | None
    retain_all_versions: bool
    linked_pms_component_id: str | None
    alert_lead_overrides: str | None
    regulatory_anchor: str | None
    legacy_remarks: str | None
    print_order: int
    is_active: bool

    def insert_params(self, *, parent_id: str | None, actor_id: str) -> list[Any]:
        return [
            self.canonical_code,
            self.section_id,
            self.display_name,
            self.short_name,
            self.print_section_label,
            self.validity_type,
            self.cadence_months,
            self.cadence_custom_days,
            self.issuing_authority_type,
            int(self.is_class_tracked),
            self.submission_scope,
            parent_id,
            self.relationship_type_default,
            json.dumps(list(self.applicable_ship_types)),
            int(self.mandatory_for_all_vessels),
            self.applicability_mode,
            json.dumps(list(self.specific_vessel_ids)),
            int(self.parent_supports_dynamic_children),
            self.age_gate_max_years,
            int(self.retain_all_versions),
            self.linked_pms_component_id,
            self.alert_lead_overrides,
            self.regulatory_anchor,
            self.legacy_remarks,
            self.print_order,
            int(self.is_active),
            actor_id,
            actor_id,
        ]

    def audit_after_payload(self, *, catalog_id: str, parent_id: str | None) -> dict[str, Any]:
        section_code, section_name = SECTION_LOOKUP.get(self.section_id, (None, None))
        return {
            "id": catalog_id,
            "canonicalCode": self.canonical_code,
            "sectionId": self.section_id,
            "sectionCode": section_code,
            "sectionName": section_name,
            "displayName": self.display_name,
            "shortName": self.short_name,
            "printSectionLabel": self.print_section_label,
            "validityType": self.validity_type,
            "cadenceMonths": self.cadence_months,
            "cadenceCustomDays": self.cadence_custom_days,
            "issuingAuthorityType": self.issuing_authority_type,
            "isClassTracked": self.is_class_tracked,
            "submissionScope": self.submission_scope,
            "parentId": parent_id,
            "relationshipTypeDefault": self.relationship_type_default,
            "applicableShipTypes": list(self.applicable_ship_types),
            "mandatoryForAllVessels": self.mandatory_for_all_vessels,
            "applicabilityMode": self.applicability_mode,
            "specificVesselIds": list(self.specific_vessel_ids),
            "parentSupportsDynamicChildren": self.parent_supports_dynamic_children,
            "ageGateMaxYears": self.age_gate_max_years,
            "retainAllVersions": self.retain_all_versions,
            "linkedPmsComponentId": self.linked_pms_component_id,
            "alertLeadOverrides": _json_loads(self.alert_lead_overrides),
            "regulatoryAnchor": self.regulatory_anchor,
            "legacyRemarks": self.legacy_remarks,
            "printOrder": self.print_order,
            "isActive": self.is_active,
        }


@dataclass(frozen=True)
class CatalogWorkshopSeedResult:
    created_codes: tuple[str, ...]
    skipped_codes: tuple[str, ...]
    would_create_codes: tuple[str, ...] = ()
    would_skip_codes: tuple[str, ...] = ()

    @property
    def created_count(self) -> int:
        return len(self.created_codes)

    @property
    def skipped_count(self) -> int:
        return len(self.skipped_codes)

    @property
    def would_create_count(self) -> int:
        return len(self.would_create_codes)

    @property
    def would_skip_count(self) -> int:
        return len(self.would_skip_codes)


def load_catalog_workshop_rows(path: str | Path) -> list[CatalogWorkshopSeedRow]:
    with Path(path).open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fieldnames = set(reader.fieldnames or ())
        missing = sorted(REQUIRED_CSV_COLUMNS - fieldnames)
        if missing:
            raise ValueError(f"Catalog workshop CSV missing required column(s): {', '.join(missing)}")
        rows = [_row_from_csv(index, row) for index, row in enumerate(reader, start=2)]

    if not rows:
        raise ValueError("Catalog workshop CSV contains no catalog rows.")
    _validate_unique_codes(rows)
    return rows


def seed_certs_catalog_rows(
    cursor,
    rows: list[CatalogWorkshopSeedRow],
    *,
    actor_id: str,
    approval_ref: str,
    dry_run: bool,
) -> CatalogWorkshopSeedResult:
    if not rows:
        return CatalogWorkshopSeedResult(created_codes=(), skipped_codes=())

    lookup_codes = {row.canonical_code for row in rows}
    lookup_codes.update(row.parent_canonical_code for row in rows if row.parent_canonical_code)
    existing_ids = _load_existing_ids(cursor, sorted(lookup_codes))
    created_codes: list[str] = []
    skipped_codes: list[str] = []
    would_create_codes: list[str] = []
    would_skip_codes: list[str] = []

    for row in rows:
        if row.canonical_code in existing_ids:
            skipped_codes.append(row.canonical_code)
            would_skip_codes.append(row.canonical_code)
            continue

        parent_id = existing_ids.get(row.parent_canonical_code) if row.parent_canonical_code else None
        if row.parent_canonical_code and parent_id is None:
            raise RuntimeError(f"Parent row {row.parent_canonical_code} must exist before seeding {row.canonical_code}.")

        would_create_codes.append(row.canonical_code)
        if dry_run:
            existing_ids[row.canonical_code] = f"<pending:{row.canonical_code}>"
            continue

        cursor.execute(_insert_sql(), row.insert_params(parent_id=parent_id, actor_id=actor_id))
        catalog_id = str(cursor.fetchone()[0])
        existing_ids[row.canonical_code] = catalog_id
        created_codes.append(row.canonical_code)
        _record_create_audit(
            cursor,
            row=row,
            catalog_id=catalog_id,
            parent_id=parent_id,
            actor_id=actor_id,
            approval_ref=approval_ref,
        )

    return CatalogWorkshopSeedResult(
        created_codes=tuple(created_codes),
        skipped_codes=tuple(skipped_codes),
        would_create_codes=tuple(would_create_codes),
        would_skip_codes=tuple(would_skip_codes),
    )


def _row_from_csv(line_number: int, row: dict[str, str]) -> CatalogWorkshopSeedRow:
    try:
        section_id = _required_int(row, "section_id")
        if section_id not in SECTION_LOOKUP:
            raise ValueError(f"section_id must be one of {sorted(SECTION_LOOKUP)}")
        validity_type = _required_choice(row, "validity_type", VALIDITY_TYPES)
        issuing_authority_type = _required_choice(row, "issuing_authority_type", ISSUING_AUTHORITY_TYPES)
        submission_scope = _required_choice(row, "submission_scope", SUBMISSION_SCOPES)
        applicability_mode = _choice(row, "applicability_mode", APPLICABILITY_MODES, default="all_matching_type")
        applicable_ship_types = _csv_list(row.get("applicable_ship_types"), default=("all",))
        unknown_ship_types = sorted(set(applicable_ship_types) - SHIP_TYPES)
        if unknown_ship_types:
            raise ValueError(f"applicable_ship_types contains unsupported value(s): {', '.join(unknown_ship_types)}")
        specific_vessel_ids = _csv_list(row.get("specific_vessel_ids"), default=())
        if applicability_mode == "specific_vessel_ids" and not specific_vessel_ids:
            raise ValueError("specific_vessel_ids is required when applicability_mode=specific_vessel_ids")
    except ValueError as exc:
        raise ValueError(f"Catalog workshop CSV line {line_number}: {exc}") from exc

    return CatalogWorkshopSeedRow(
        canonical_code=_required_text(row, "canonical_code").upper(),
        section_id=section_id,
        display_name=_required_text(row, "display_name"),
        short_name=_optional_text(row.get("short_name")),
        print_section_label=_required_text(row, "print_section_label"),
        validity_type=validity_type,
        cadence_months=_nullable_int(row.get("cadence_months")),
        cadence_custom_days=_nullable_int(row.get("cadence_custom_days")),
        issuing_authority_type=issuing_authority_type,
        is_class_tracked=_bool(row.get("is_class_tracked"), default=False),
        submission_scope=submission_scope,
        parent_canonical_code=_optional_text(row.get("parent_canonical_code")),
        relationship_type_default=_optional_text(row.get("relationship_type_default")),
        applicable_ship_types=applicable_ship_types,
        mandatory_for_all_vessels=_bool(row.get("mandatory_for_all_vessels"), default=True),
        applicability_mode=applicability_mode,
        specific_vessel_ids=specific_vessel_ids,
        parent_supports_dynamic_children=_bool(row.get("parent_supports_dynamic_children"), default=False),
        age_gate_max_years=_nullable_int(row.get("age_gate_max_years")),
        retain_all_versions=_bool(row.get("retain_all_versions"), default=False),
        linked_pms_component_id=_optional_text(row.get("linked_pms_component_id")),
        alert_lead_overrides=_optional_json_text(row.get("alert_lead_overrides")),
        regulatory_anchor=_optional_text(row.get("regulatory_anchor")),
        legacy_remarks=_optional_text(row.get("legacy_remarks")),
        print_order=_required_int(row, "print_order"),
        is_active=_bool(row.get("is_active"), default=True),
    )


def _load_existing_ids(cursor, canonical_codes: list[str]) -> dict[str, str]:
    placeholders = ", ".join(["%s"] * len(canonical_codes))
    cursor.execute(
        f"""
        SELECT canonical_code, CONVERT(NVARCHAR(36), catalog_id)
        FROM dbo.vims_certs_catalog_row
        WHERE canonical_code IN ({placeholders})
        """,
        canonical_codes,
    )
    return {str(code): str(catalog_id) for code, catalog_id in cursor.fetchall()}


def _insert_sql() -> str:
    return """
        INSERT INTO dbo.vims_certs_catalog_row (
            canonical_code, section_id, display_name, short_name, print_section_label,
            validity_type, cadence_months, cadence_custom_days, issuing_authority_type,
            is_class_tracked, submission_scope, parent_id, relationship_type_default,
            applicable_ship_types, mandatory_for_all_vessels, applicability_mode,
            specific_vessel_ids, parent_supports_dynamic_children, age_gate_max_years,
            retain_all_versions, linked_pms_component_id, alert_lead_overrides,
            regulatory_anchor, legacy_remarks, print_order, is_active, created_by, updated_by
        )
        OUTPUT inserted.catalog_id
        VALUES (
            %s, %s, %s, %s, %s,
            %s, %s, %s, %s,
            %s, %s, %s, %s,
            %s, %s, %s,
            %s, %s, %s,
            %s, %s, %s,
            %s, %s, %s, %s, %s, %s
        )
    """


def _record_create_audit(
    cursor,
    *,
    row: CatalogWorkshopSeedRow,
    catalog_id: str,
    parent_id: str | None,
    actor_id: str,
    approval_ref: str,
) -> None:
    cursor.execute(
        """
        INSERT INTO dbo.vims_certs_audit_log (
            actor_user_id, actor_role, action, entity_type, entity_id,
            before_json, after_json, reason, event_metadata
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """,
        [
            actor_id,
            "SYSTEM",
            "create_catalog_row",
            "catalog_row",
            catalog_id,
            None,
            json.dumps(row.audit_after_payload(catalog_id=catalog_id, parent_id=parent_id), default=str),
            f"Phase 1.12 catalog workshop seed approved by {approval_ref}.",
            json.dumps({"source": "management.seed_certs_catalog", "phase": "1.12", "approvalRef": approval_ref}),
        ],
    )


def _validate_unique_codes(rows: list[CatalogWorkshopSeedRow]) -> None:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for row in rows:
        if row.canonical_code in seen:
            duplicates.add(row.canonical_code)
        seen.add(row.canonical_code)
    if duplicates:
        raise ValueError(f"Catalog workshop CSV contains duplicate canonical_code values: {', '.join(sorted(duplicates))}")


def _required_text(row: dict[str, str], key: str) -> str:
    value = str(row.get(key) or "").strip()
    if not value:
        raise ValueError(f"{key} is required")
    return value


def _optional_text(value: str | None) -> str | None:
    text = str(value or "").strip()
    return text or None


def _required_int(row: dict[str, str], key: str) -> int:
    value = _required_text(row, key)
    try:
        return int(value)
    except ValueError as exc:
        raise ValueError(f"{key} must be an integer") from exc


def _nullable_int(value: str | None) -> int | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        return int(text)
    except ValueError as exc:
        raise ValueError(f"{text} must be an integer") from exc


def _required_choice(row: dict[str, str], key: str, choices: set[str]) -> str:
    return _choice(row, key, choices, default=None)


def _choice(row: dict[str, str], key: str, choices: set[str], *, default: str | None) -> str:
    value = str(row.get(key) or default or "").strip()
    if value not in choices:
        raise ValueError(f"{key} must be one of {', '.join(sorted(choices))}")
    return value


def _bool(value: str | None, *, default: bool) -> bool:
    text = str(value or "").strip().lower()
    if not text:
        return default
    if text in {"1", "true", "yes", "y"}:
        return True
    if text in {"0", "false", "no", "n"}:
        return False
    raise ValueError(f"{value} must be true or false")


def _csv_list(value: str | None, *, default: tuple[str, ...]) -> tuple[str, ...]:
    text = str(value or "").strip()
    if not text:
        return default
    if text.startswith("["):
        loaded = json.loads(text)
        return tuple(str(item).strip() for item in loaded if str(item).strip())
    return tuple(item.strip() for item in text.replace(";", ",").split(",") if item.strip())


def _optional_json_text(value: str | None) -> str | None:
    text = str(value or "").strip()
    if not text:
        return None
    json.loads(text)
    return text


def _json_loads(value: str | None) -> Any:
    if not value:
        return None
    return json.loads(value)
