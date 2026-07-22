from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Any


SEED_ACTOR_ID = "seed_class_code_mappings"
VALID_CERT_OR_SURVEY_KINDS = {"renewal", "intermediate", "annual", "periodic", "n/a"}


@dataclass(frozen=True)
class ClassCodeMappingSeedRow:
    class_society: str
    class_code_or_name: str
    catalog_code: str
    cert_or_survey_kind: str
    notes: str

    def normalized_key(self) -> tuple[str, str]:
        return (self.class_society.upper(), _normal_key(self.class_code_or_name))

    def insert_params(self, *, catalog_id: str, version: int, actor_id: str) -> list[Any]:
        return [
            self.class_society.upper(),
            self.class_code_or_name,
            catalog_id,
            self.cert_or_survey_kind,
            self.notes,
            version,
            actor_id,
            actor_id,
        ]

    def audit_after_payload(self, *, mapping_id: str, catalog_id: str, version: int) -> dict[str, Any]:
        return {
            "id": mapping_id,
            "classSociety": self.class_society.upper(),
            "classCodeOrName": self.class_code_or_name,
            "catalogId": catalog_id,
            "catalogCode": self.catalog_code,
            "certOrSurveyKind": self.cert_or_survey_kind,
            "notes": self.notes,
            "version": version,
            "active": True,
        }


@dataclass(frozen=True)
class ClassCodeMappingSeedResult:
    created: tuple[str, ...]
    skipped: tuple[str, ...]
    missing_catalog_codes: tuple[str, ...]
    would_create: tuple[str, ...] = ()
    would_skip: tuple[str, ...] = ()

    @property
    def created_count(self) -> int:
        return len(self.created)

    @property
    def skipped_count(self) -> int:
        return len(self.skipped)

    @property
    def missing_catalog_count(self) -> int:
        return len(self.missing_catalog_codes)

    @property
    def would_create_count(self) -> int:
        return len(self.would_create)

    @property
    def would_skip_count(self) -> int:
        return len(self.would_skip)


KR_CLASS_CODE_MAPPING_ROWS: tuple[ClassCodeMappingSeedRow, ...] = (
    ClassCodeMappingSeedRow("KR", "CC", "CLASS-COC", "n/a", "KR Certificate of Class."),
    ClassCodeMappingSeedRow("KR", "CG2", "CLASS-CG2", "n/a", "KR Cargo Gear certificate."),
    ClassCodeMappingSeedRow("KR", "LI", "CLASS-LI", "n/a", "KR Loading Instrument certificate."),
    ClassCodeMappingSeedRow("KR", "Annual Survey", "CLASS-ANNUAL-SURVEY", "annual", "KR class annual survey."),
    ClassCodeMappingSeedRow("KR", "Intermediate Survey", "CLASS-INTERMEDIATE-SURVEY", "intermediate", "KR class intermediate survey."),
    ClassCodeMappingSeedRow("KR", "Renewal Survey", "CLASS-SPECIAL-SURVEY", "renewal", "KR class renewal survey."),
    ClassCodeMappingSeedRow("KR", "Special Survey", "CLASS-SPECIAL-SURVEY", "renewal", "KR class special survey."),
    ClassCodeMappingSeedRow("KR", "Docking Survey", "CLASS-DOCKING-SURVEY", "periodic", "KR docking survey."),
    ClassCodeMappingSeedRow("KR", "No.1 Aux.Boiler Survey", "CLASS-BOILER-SURVEY", "periodic", "KR auxiliary boiler survey."),
    ClassCodeMappingSeedRow("KR", "No.1 Propeller Shaft Survey", "CLASS-PROP-SHAFT-SURVEY", "periodic", "KR propeller shaft survey."),
    ClassCodeMappingSeedRow("KR", "ILL", "STAT-INTERNATIONAL-LOADLINE-CERTIFICATE", "n/a", "KR International Load Line certificate."),
    ClassCodeMappingSeedRow("KR", "IOPP-A", "STAT-INTERNATIONAL-OIL-POLLUTION-PREVENTION-IOPP-WITH", "n/a", "KR IOPP Form A certificate."),
    ClassCodeMappingSeedRow("KR", "IAPP", "STAT-INTERNATIONAL-AIR-POLLUTION-PREVENTION-IAPP-WITH", "n/a", "KR IAPP certificate."),
    ClassCodeMappingSeedRow("KR", "ISPP", "STAT-INTERNATIONAL-SEWAGE-POLLUTION-PREVENTION-ISPP", "n/a", "KR ISPP certificate."),
    ClassCodeMappingSeedRow("KR", "BWM", "STAT-INTERNATIONAL-BALLAST-WATER-CONVENTION-CERTIFICA", "n/a", "KR Ballast Water Management certificate."),
    ClassCodeMappingSeedRow("KR", "IEE", "STAT-INTERNATIONAL-ENERGY-EFFICIENCY-CERTIFICATE-IEEC", "n/a", "KR International Energy Efficiency certificate."),
    ClassCodeMappingSeedRow("KR", "IAFS", "STAT-ANTI-FOULING-CERTIFICATE", "n/a", "KR Anti-Fouling certificate."),
    ClassCodeMappingSeedRow("KR", "IMSBC", "STAT-CERTIFICATE-OF-COMPLIANCE-WITH-THE-IMSBC-CODE", "n/a", "KR IMSBC compliance certificate."),
    ClassCodeMappingSeedRow("KR", "CDG", "STAT-DOC-OF-COMPLIANCE-FOR-SPECIAL-REQUIREMENTS-FOR-S", "n/a", "KR dangerous goods document of compliance."),
    ClassCodeMappingSeedRow("KR", "VGP", "TRADE-US-VESSEL-GENERAL-PERMIT-VGP", "n/a", "KR Vessel General Permit row."),
    ClassCodeMappingSeedRow("KR", "IIHM", "MISC-IHM-CERTIFICATE-IHM-STATEMENT-OF-COMPLIANCE", "n/a", "KR IHM certificate."),
    ClassCodeMappingSeedRow("KR", "IHM(EU)", "MISC-IHM-CERTIFICATE-IHM-STATEMENT-OF-COMPLIANCE", "n/a", "KR EU IHM certificate."),
    ClassCodeMappingSeedRow("KR", "IGPP", "MISC-VOLUNTARY-STATEMENT-OF-COMPLIANCE-WITH-MARPOL-AN", "n/a", "KR garbage pollution prevention certificate; nearest approved catalog row."),
    ClassCodeMappingSeedRow("KR", "SC", "STAT-CARGO-SHIP-SAFETY-CONSTRUCTION", "n/a", "KR Cargo Ship Safety Construction certificate."),
    ClassCodeMappingSeedRow("KR", "SE", "STAT-CARGO-SHIP-SAFETY-EQUIPMENT", "n/a", "KR Cargo Ship Safety Equipment certificate."),
    ClassCodeMappingSeedRow("KR", "SR", "STAT-CARGO-SHIP-SAFETY-RADIO", "n/a", "KR Cargo Ship Safety Radio certificate."),
    ClassCodeMappingSeedRow("KR", "Cargo Gear Survey(Annual)", "STAT-CARGO-GEAR-ANNUAL-SURVEY", "annual", "KR cargo gear annual survey."),
    ClassCodeMappingSeedRow("KR", "Cargo Ship Safety Construction Annual Survey", "TRADE-CARGO-SHIP-SAFETY-CONSTRUCTION-ANNUAL-PERIODICAL", "annual", "KR safety construction annual survey."),
    ClassCodeMappingSeedRow("KR", "Cargo Ship Safety Construction Intermediate Survey", "TRADE-CARGO-SHIP-SAFETY-CONSTRUCTION-ANNUAL-PERIODICAL", "intermediate", "KR safety construction intermediate survey."),
    ClassCodeMappingSeedRow("KR", "Cargo Ship Safety Construction Renewal Survey", "STAT-CARGO-SHIP-SAFETY-CONSTRUCTION", "renewal", "KR safety construction renewal survey."),
    ClassCodeMappingSeedRow("KR", "Cargo Ship Safety Equipment Annual Survey", "TRADE-CARGO-SHIP-SAFETY-EQUIPMENT-ANNUAL-PERIODICAL", "annual", "KR safety equipment annual survey."),
    ClassCodeMappingSeedRow("KR", "Cargo Ship Safety Equipment Periodical Survey", "TRADE-CARGO-SHIP-SAFETY-EQUIPMENT-ANNUAL-PERIODICAL", "periodic", "KR safety equipment periodical survey."),
    ClassCodeMappingSeedRow("KR", "Cargo Ship Safety Equipment Renewal Survey", "STAT-CARGO-SHIP-SAFETY-EQUIPMENT", "renewal", "KR safety equipment renewal survey."),
    ClassCodeMappingSeedRow("KR", "Cargo Ship Safety Radio Periodical Survey", "TRADE-CARGO-SHIP-SAFETY-RADIO-ANNUAL-PERIODICAL", "periodic", "KR safety radio periodical survey."),
    ClassCodeMappingSeedRow("KR", "Cargo Ship Safety Radio Renewal Survey", "STAT-CARGO-SHIP-SAFETY-RADIO", "renewal", "KR safety radio renewal survey."),
    ClassCodeMappingSeedRow("KR", "Oil Pollution Prevention Annual Survey", "TRADE-IOPP-ANNUAL-INTERMEDIATE", "annual", "KR IOPP annual survey."),
    ClassCodeMappingSeedRow("KR", "Oil Pollution Prevention Intermediate Survey", "TRADE-IOPP-ANNUAL-INTERMEDIATE", "intermediate", "KR IOPP intermediate survey."),
    ClassCodeMappingSeedRow("KR", "Oil Pollution Prevention Renewal Survey", "STAT-INTERNATIONAL-OIL-POLLUTION-PREVENTION-IOPP-WITH", "renewal", "KR IOPP renewal survey."),
    ClassCodeMappingSeedRow("KR", "Air Pollution Prevention Annual Survey", "TRADE-IAPP-ANNUAL-PERIODICAL", "annual", "KR IAPP annual survey."),
    ClassCodeMappingSeedRow("KR", "Air Pollution Prevention Intermediate Survey", "TRADE-IAPP-ANNUAL-PERIODICAL", "intermediate", "KR IAPP intermediate survey."),
    ClassCodeMappingSeedRow("KR", "Air Pollution Prevention Renewal Survey", "STAT-INTERNATIONAL-AIR-POLLUTION-PREVENTION-IAPP-WITH", "renewal", "KR IAPP renewal survey."),
    ClassCodeMappingSeedRow("KR", "Sewage Pollution Prevention Renewal Survey", "STAT-INTERNATIONAL-SEWAGE-POLLUTION-PREVENTION-ISPP", "renewal", "KR ISPP renewal survey."),
    ClassCodeMappingSeedRow("KR", "Garbage Pollution Prevention Renewal Survey", "MISC-VOLUNTARY-STATEMENT-OF-COMPLIANCE-WITH-MARPOL-AN", "renewal", "KR garbage pollution prevention renewal survey; nearest approved catalog row."),
    ClassCodeMappingSeedRow("KR", "Ballast Water Management Annual Survey", "STAT-INTERNATIONAL-BALLAST-WATER-CONVENTION-CERTIFICA", "annual", "KR ballast water annual survey."),
    ClassCodeMappingSeedRow("KR", "Ballast Water Management Intermediate Survey", "STAT-INTERNATIONAL-BALLAST-WATER-CONVENTION-CERTIFICA", "intermediate", "KR ballast water intermediate survey."),
    ClassCodeMappingSeedRow("KR", "Ballast Water Management Renewal Survey", "STAT-INTERNATIONAL-BALLAST-WATER-CONVENTION-CERTIFICA", "renewal", "KR ballast water renewal survey."),
    ClassCodeMappingSeedRow("KR", "Maritime Solid Bulk Cargoes Code Renewal Survey", "STAT-CERTIFICATE-OF-COMPLIANCE-WITH-THE-IMSBC-CODE", "renewal", "KR IMSBC renewal survey."),
    ClassCodeMappingSeedRow("KR", "Inventory of Hazardous Materials Occasional Survey", "MISC-IHM-CERTIFICATE-IHM-STATEMENT-OF-COMPLIANCE", "periodic", "KR IHM occasional survey."),
    ClassCodeMappingSeedRow("KR", "Inventory of Hazardous Materials Renewal Survey", "MISC-IHM-CERTIFICATE-IHM-STATEMENT-OF-COMPLIANCE", "renewal", "KR IHM renewal survey."),
)

CLASS_CODE_MAPPING_ROWS: tuple[ClassCodeMappingSeedRow, ...] = KR_CLASS_CODE_MAPPING_ROWS


def validate_class_code_mapping_seed_rows(rows: tuple[ClassCodeMappingSeedRow, ...] = CLASS_CODE_MAPPING_ROWS) -> None:
    seen: set[tuple[str, str]] = set()
    for row in rows:
        key = row.normalized_key()
        if key in seen:
            raise ValueError(f"Duplicate class-code mapping seed row: {row.class_society} {row.class_code_or_name}")
        seen.add(key)
        if row.cert_or_survey_kind not in VALID_CERT_OR_SURVEY_KINDS:
            raise ValueError(f"Invalid cert_or_survey_kind for {row.class_code_or_name}: {row.cert_or_survey_kind}")


def seed_class_code_mappings(
    cursor,
    rows: tuple[ClassCodeMappingSeedRow, ...] = CLASS_CODE_MAPPING_ROWS,
    *,
    actor_id: str = SEED_ACTOR_ID,
    dry_run: bool = True,
) -> ClassCodeMappingSeedResult:
    validate_class_code_mapping_seed_rows(rows)
    catalog_ids = _load_catalog_ids(cursor, rows)
    missing_catalog_codes = tuple(sorted({row.catalog_code for row in rows if row.catalog_code not in catalog_ids}))
    active_keys = _load_active_mapping_keys(cursor, rows)
    next_versions = _load_next_versions(cursor, rows)

    created: list[str] = []
    skipped: list[str] = []
    would_create: list[str] = []
    would_skip: list[str] = []

    for row in rows:
        label = _row_label(row)
        if row.normalized_key() in active_keys:
            skipped.append(label)
            would_skip.append(label)
            continue
        if row.catalog_code in missing_catalog_codes:
            continue

        would_create.append(label)
        if dry_run:
            continue

        version = next_versions.get(row.normalized_key(), 0) + 1
        cursor.execute(_insert_sql(), row.insert_params(catalog_id=catalog_ids[row.catalog_code], version=version, actor_id=actor_id))
        mapping_id = str(cursor.fetchone()[0])
        created.append(label)
        next_versions[row.normalized_key()] = version
        _record_create_audit(
            cursor,
            row=row,
            mapping_id=mapping_id,
            catalog_id=catalog_ids[row.catalog_code],
            version=version,
            actor_id=actor_id,
        )

    return ClassCodeMappingSeedResult(
        created=tuple(created),
        skipped=tuple(skipped),
        missing_catalog_codes=missing_catalog_codes,
        would_create=tuple(would_create),
        would_skip=tuple(would_skip),
    )


def _load_catalog_ids(cursor, rows: tuple[ClassCodeMappingSeedRow, ...]) -> dict[str, str]:
    catalog_codes = sorted({row.catalog_code for row in rows})
    placeholders = ", ".join(["%s"] * len(catalog_codes))
    cursor.execute(
        f"""
        SELECT canonical_code, CONVERT(NVARCHAR(36), catalog_id)
        FROM dbo.vims_certs_catalog_row
        WHERE canonical_code IN ({placeholders})
        """,
        catalog_codes,
    )
    return {str(code): str(catalog_id) for code, catalog_id in cursor.fetchall()}


def _load_active_mapping_keys(cursor, rows: tuple[ClassCodeMappingSeedRow, ...]) -> set[tuple[str, str]]:
    societies = sorted({row.class_society.upper() for row in rows})
    placeholders = ", ".join(["%s"] * len(societies))
    cursor.execute(
        f"""
        SELECT class_society, class_code_or_name
        FROM dbo.vims_certs_class_code_mapping
        WHERE class_society IN ({placeholders})
          AND active = 1
        """,
        societies,
    )
    return {(str(society).upper(), _normal_key(code)) for society, code in cursor.fetchall()}


def _load_next_versions(cursor, rows: tuple[ClassCodeMappingSeedRow, ...]) -> dict[tuple[str, str], int]:
    societies = sorted({row.class_society.upper() for row in rows})
    placeholders = ", ".join(["%s"] * len(societies))
    cursor.execute(
        f"""
        SELECT class_society, class_code_or_name, COALESCE(MAX(version), 0)
        FROM dbo.vims_certs_class_code_mapping
        WHERE class_society IN ({placeholders})
        GROUP BY class_society, class_code_or_name
        """,
        societies,
    )
    return {(str(society).upper(), _normal_key(code)): int(version or 0) for society, code, version in cursor.fetchall()}


def _insert_sql() -> str:
    return """
        INSERT INTO dbo.vims_certs_class_code_mapping (
            class_society, class_code_or_name, catalog_id, cert_or_survey_kind,
            notes, version, active, created_by, updated_by
        )
        OUTPUT inserted.mapping_id
        VALUES (%s, %s, %s, %s, %s, %s, 1, %s, %s)
    """


def _record_create_audit(
    cursor,
    *,
    row: ClassCodeMappingSeedRow,
    mapping_id: str,
    catalog_id: str,
    version: int,
    actor_id: str,
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
            "add_class_mapping",
            "class_code_mapping",
            mapping_id,
            None,
            json.dumps(row.audit_after_payload(mapping_id=mapping_id, catalog_id=catalog_id, version=version), default=str),
            "Approved KR baseline class-code mapping seed.",
            json.dumps({"source": "management.seed_class_code_mappings", "society": row.class_society.upper()}),
        ],
    )


def _normal_key(value: Any) -> str:
    return " ".join(str(value or "").strip().upper().split())


def _row_label(row: ClassCodeMappingSeedRow) -> str:
    return f"{row.class_society.upper()} {row.class_code_or_name} -> {row.catalog_code}"
